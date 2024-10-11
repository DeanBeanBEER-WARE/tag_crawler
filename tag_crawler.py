import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import re
from collections import deque
import hashlib
import logging
import time
import urllib.robotparser
import html  # For HTML escaping
import certifi

# Define a constant USER_AGENT
USER_AGENT = 'Mozilla/5.0 (compatible; HeadingCrawler/1.0; +http://yourdomain.com/crawler)'

class HeadingNode:
    """
    Class representing a node in the heading tree.

    Attributes:
        level (int): The level of the heading (1-6 corresponding to h1-h6).
        title (str): The text of the heading.
        children (list): A list of child HeadingNode objects.
    """

    def __init__(self, level, title):
        """
        Initializes a new HeadingNode.

        Args:
            level (int): The level of the heading.
            title (str): The text of the heading.
        """
        self.level = level  # Heading level (1-6)
        self.title = title  # Text of the heading
        self.children = []  # List of child headings

    def add_child(self, child):
        """
        Adds a child to the current node.

        Args:
            child (HeadingNode): The child node to add.
        """
        self.children.append(child)

def get_headings(url):
    """
    Extracts all headings (h1 to h6) and the page title from the given URL.

    Args:
        url (str): The URL of the webpage to extract headings from.

    Returns:
        tuple: A tuple containing the page title (str) and a list of heading tuples.
    """
    try:
        headers = {
            'User-Agent': USER_AGENT
        }
        response = requests.get(url, headers=headers, timeout=10, verify=certifi.where())
        response.raise_for_status()  # Checks if the request was successful
    except requests.RequestException as e:
        logging.error(f"Error fetching URL '{url}': {e}")
        return ("No Title", [])  # Returns a default title and empty headings list

    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the page title
    title_tag = soup.find('title')
    page_title = title_tag.get_text(strip=True) if title_tag else f"Heading Structure for {url}"

    headings = []
    # Find all heading tags h1 to h6 in the order they appear
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        level = int(tag.name[1])  # Extracts the level from the tag name, e.g., h2 -> 2
        title = tag.get_text(strip=True)  # Extracts the text without leading/trailing whitespace
        headings.append((level, title))
    
    return (page_title, headings)

def build_tree(headings):
    """
    Builds a hierarchical tree from the list of headings.

    Args:
        headings (list): A list of tuples (level, title) representing the headings.

    Returns:
        HeadingNode: The root node of the constructed heading tree.
    """
    root = HeadingNode(0, "Root")  # Virtual root node with level 0
    stack = [root]  # Stack to keep track of the current path in the tree

    for level, title in headings:
        node = HeadingNode(level, title)  # Creates a new node for the heading
        
        # Finds the appropriate parent node by traversing the stack
        while stack and stack[-1].level >= level:
            stack.pop()  # Removes nodes from the stack that have a higher or equal level
        
        # The current node is a child of the last node in the stack
        stack[-1].add_child(node)
        stack.append(node)  # Adds the current node to the stack
    
    return root

def sanitize_filename(url):
    """
    Generates a safe filename from a URL by replacing non-alphanumeric characters.

    Args:
        url (str): The URL to convert into a filename.

    Returns:
        str: A sanitized filename.
    """
    parsed_url = urlparse(url)
    path = parsed_url.path.strip('/')
    if not path:
        path = 'home'
    safe_path = re.sub(r'[^a-zA-Z0-9_-]', '_', path)
    # Generates a hash of the URL for uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{safe_path}_{url_hash}.html"

def is_internal_link(link, base_domain):
    """
    Determines if a link is internal (i.e., belongs to the same domain).

    Args:
        link (str): The URL to check.
        base_domain (str): The base domain for comparison.

    Returns:
        bool: True if the link is internal, False otherwise.
    """
    parsed_link = urlparse(link)
    return (parsed_link.netloc == base_domain) or (parsed_link.netloc == '')

def is_allowed(url, user_agent=USER_AGENT):
    """
    Checks if crawling the URL is allowed according to robots.txt.

    Args:
        url (str): The URL to check.
        user_agent (str): The User-Agent to use for the check.

    Returns:
        bool: True if crawling is allowed, False otherwise.
    """
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        allowed = rp.can_fetch(user_agent, url)
        print(f"Checking robots.txt for '{url}': {'Allowed' if allowed else 'Disallowed'}")
        return allowed
    except Exception as e:
        logging.error(f"Error reading robots.txt for '{url}': {e}")
        return False  # Defaults to "disallow" if robots.txt cannot be fetched

def crawl_website(base_url, max_pages=100, max_depth=5, delay=1):
    """
    Crawls the website starting from the base URL and collects all internal subpage URLs.

    Args:
        base_url (str): The main domain URL to start crawling from.
        max_pages (int, optional): Maximum number of pages to crawl. Defaults to 100.
        max_depth (int, optional): Maximum depth for crawling. Defaults to 5.
        delay (int, optional): Delay in seconds between requests. Defaults to 1.

    Returns:
        set: A set of unique internal subpage URLs.
    """
    visited = set()  # Set to keep track of visited URLs
    queue = deque()  # Queue for BFS traversal
    queue.append((base_url, 0))  # URL with current depth
    visited.add(base_url)

    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    while queue and len(visited) < max_pages:
        current_url, depth = queue.popleft()
        if depth > max_depth:
            continue

        # Check robots.txt before crawling
        if not is_allowed(current_url):
            print(f"Skipping '{current_url}' due to robots.txt restrictions.")
            continue

        print(f"Crawling: {current_url} (Depth {depth})")
        try:
            headers = {
                'User-Agent': USER_AGENT
            }
            response = requests.get(current_url, headers=headers, timeout=10, verify=certifi.where())
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching URL '{current_url}': {e}")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all anchor tags with href attributes
        for link_tag in soup.find_all('a', href=True):
            href = link_tag.get('href')
            # Resolve relative URLs
            href = urljoin(current_url, href)
            # Remove URL fragments
            href = href.split('#')[0]
            # Remove trailing slash
            href = href.rstrip('/')

            # Check if the link is internal
            if is_internal_link(href, base_domain):
                # Normalize the URL
                parsed_href = urlparse(href)
                # Handle URLs without a path by defaulting to '/'
                path = parsed_href.path if parsed_href.path else '/'
                normalized_href = f"{parsed_href.scheme}://{parsed_href.netloc}{path}"
                if normalized_href not in visited:
                    print(f"Found internal link: {normalized_href}")
                    visited.add(normalized_href)
                    queue.append((normalized_href, depth + 1))
        
        # Politeness delay
        time.sleep(delay)  # Pause for 'delay' seconds between requests

    return visited

def create_output_directory(base_url):
    """
    Creates an output directory named after the main domain in the user's Documents folder.

    Args:
        base_url (str): The main domain URL.

    Returns:
        str: The path to the created directory.
    """
    # Get the user's home directory
    home_dir = os.path.expanduser("~")
    # Define the Documents directory path
    documents_dir = os.path.join(home_dir, "Documents")
    # Check if Documents directory exists, if not, use home directory
    if not os.path.exists(documents_dir):
        documents_dir = home_dir
    # Parse the base URL to get the domain name
    parsed_url = urlparse(base_url)
    domain_name = parsed_url.netloc
    # Remove 'www.' prefix for a cleaner directory name
    if domain_name.startswith('www.'):
        domain_name = domain_name[4:]
    # Define the directory path inside Documents
    directory_path = os.path.join(documents_dir, domain_name)
    # Create the directory if it does not exist
    os.makedirs(directory_path, exist_ok=True)
    return directory_path

def generate_combined_html(output_path, page_structures):
    """
    Generates a combined HTML document with buttons for each subpage and their heading structures.

    Args:
        output_path (str): The path where the HTML document should be saved.
        page_structures (dict): A dictionary containing the heading structures of each subpage.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write the beginning of the HTML document
        f.write("<!DOCTYPE html>\n")
        f.write("<html lang=\"en\">\n")  # Set language to English
        f.write("<head>\n")
        f.write("<meta charset=\"UTF-8\">\n")
        f.write("<title>Heading Structures</title>\n")
        f.write("""
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        .button-container {
            margin-bottom: 20px;
        }
        .button-container button {
            padding: 10px 20px;
            margin-right: 10px;
            margin-bottom: 10px;
            border: none;
            background-color: #007BFF;
            color: white;
            cursor: pointer;
            border-radius: 4px;
            transition: background-color 0.3s;
        }
        .button-container button:hover {
            background-color: #0056b3;
        }
        .content {
            display: none; /* All content sections are hidden by default */
            margin-top: 20px;
        }
        .active {
            display: block; /* Visible when the active class is added */
        }
        .ok {
            color: green;
        }
        .error {
            color: red;
        }
        .heading {
            margin: 5px 0;
        }
        /* Indentation based on heading level */
        .heading.level-1 {
            margin-left: 0px;
        }
        .heading.level-2 {
            margin-left: 20px;
        }
        .heading.level-3 {
            margin-left: 40px;
        }
        .heading.level-4 {
            margin-left: 60px;
        }
        .heading.level-5 {
            margin-left: 80px;
        }
        .heading.level-6 {
            margin-left: 100px;
        }
        /* Styles for the report section */
        .report-item.ok {
            color: green;
            margin: 5px 0;
        }
        .report-item.error {
            color: red;
            margin: 5px 0;
        }
    </style>
    """)
        f.write("</head>\n<body>\n")
        f.write("<h1>Heading Structures</h1>\n")
        f.write("<div class=\"button-container\">\n")

        # Write the buttons for each subpage
        for idx, (url, data) in enumerate(page_structures.items()):
            # Extract the last segment of the URL path for the button label
            parsed_url = urlparse(url)
            path_segments = parsed_url.path.strip('/').split('/')
            if path_segments and path_segments[-1]:
                button_label = path_segments[-1]
            else:
                button_label = 'home'
            safe_id = f"page{idx}"
            # Escape special characters in the button label to prevent HTML issues
            escaped_label = html.escape(button_label, quote=True)
            f.write(f"  <button type=\"button\" onclick=\"toggleContent('{safe_id}')\">{escaped_label}</button>\n")

        # Add the Report button
        f.write(f"  <button type=\"button\" onclick=\"toggleContent('report')\">Report</button>\n")
        f.write("</div>\n")

        # Write the content sections for each subpage
        for idx, (url, data) in enumerate(page_structures.items()):
            page_title = data['title']
            headings = data['headings']
            safe_id = f"page{idx}"
            f.write(f"<div id=\"{safe_id}\" class=\"content\">\n")
            # Escape special characters in the page title
            escaped_page_title = html.escape(page_title, quote=True)
            f.write(f"  <h2>{escaped_page_title}</h2>\n")
            f.write("  <div>\n")
            if not headings:
                f.write("    <p>No headings found.</p>\n")
            else:
                # Build the heading tree
                tree = build_tree(headings)
                # Initialize a list to track errors
                errors_found = []
                # Recursively write the tree to HTML and track errors
                write_tree_html(tree, f, parent_level=0, errors_found=errors_found)
                # Update the error flags based on errors_found
                if errors_found:
                    page_structures[url]['error_flags'].append(True)
            f.write("  </div>\n")
            f.write("</div>\n")

        # Write the content section for the Report
        f.write("<div id=\"report\" class=\"content\">\n")
        f.write("  <h2>Report</h2>\n")
        f.write("  <div>\n")
        f.write("    <ul>\n")
        for idx, (url, data) in enumerate(page_structures.items()):
            # Extract the last segment of the URL path for the report label
            parsed_url = urlparse(url)
            path_segments = parsed_url.path.strip('/').split('/')
            if path_segments and path_segments[-1]:
                report_label = path_segments[-1]
            else:
                report_label = 'home'
            # Determine the color based on whether the page has errors
            has_error = any(data.get('error_flags', []))
            css_class = "error" if has_error else "ok"
            escaped_label = html.escape(report_label, quote=True)
            f.write(f"      <li class=\"report-item {css_class}\">{escaped_label}</li>\n")
        f.write("    </ul>\n")
        f.write("  </div>\n")
        f.write("</div>\n")

        # JavaScript to control the display of content sections
        f.write("""
<script>
    function toggleContent(id) {
        var content = document.getElementById(id);
        if (content.classList.contains('active')) {
            content.classList.remove('active');
        } else {
            // Remove 'active' from all content sections
            var contents = document.getElementsByClassName('content');
            for (var i = 0; i < contents.length; i++) {
                contents[i].classList.remove('active');
            }
            // Add 'active' to the selected content section
            content.classList.add('active');
        }
    }
    // Remove the following code to prevent any content sections from being displayed on page load
    // window.onload = function() {
    //     var firstContent = document.querySelector('.content');
    //     if (firstContent) {
    //         firstContent.classList.add('active');
    //     }
    // }
</script>
""")
        f.write("</body>\n</html>")

def write_tree_html(node, file, parent_level=0, indent=2, errors_found=None):
    """
    Recursively writes the heading tree to the HTML document.

    Args:
        node (HeadingNode): The current node in the tree.
        file (file object): The open file object to write to.
        parent_level (int, optional): The level of the parent node. Defaults to 0.
        indent (int, optional): The current indentation level. Defaults to 2.
        errors_found (list, optional): A list to track if any errors are found. Defaults to None.
    """
    if errors_found is None:
        errors_found = []

    if node.level != 0:  # Skip the virtual root node
        # Determine if the heading structure is correct
        if node.level == parent_level + 1:
            css_class = "ok"  # Correct structure
        else:
            css_class = "error"  # Structure error
            errors_found.append(True)  # Record that an error was found

        # Write the heading with the appropriate CSS classes
        # Use html.escape to handle special characters in the heading titles
        escaped_title = html.escape(node.title, quote=True)
        file.write(' ' * indent + f'<p class="heading {css_class} level-{node.level}">h{node.level} - {escaped_title}</p>\n')
    
    for child in node.children:
        # Recursive call for child nodes, passing the current node's level as the parent_level
        write_tree_html(child, file, parent_level=node.level, indent=indent + 2, errors_found=errors_found)

def main():
    """
    Main function to execute the script.

    Prompts the user for the main domain URL, crawls all internal subpages,
    extracts their heading structures, and writes them into a combined HTML document.
    """
    # Configure logging
    logging.basicConfig(filename='crawler_errors.log', level=logging.ERROR,
                        format='%(asctime)s:%(levelname)s:%(message)s')

    base_url = input("Enter the main domain URL (e.g., https://example.com): ").strip()
    
    # Validate the URL
    parsed_base = urlparse(base_url)
    if not parsed_base.scheme or not parsed_base.netloc:
        print("Invalid URL. Please include the scheme (e.g., 'https://').")
        return

    # Create the output directory in the user's Documents folder
    output_directory = create_output_directory(base_url)
    combined_html_path = os.path.join(output_directory, "heading_structures.html")
    print(f"\nThe heading structures will be saved in '{combined_html_path}'.\n")

    print("Starting to crawl the website. This may take some time depending on the size of the site...\n")
    subpages = crawl_website(base_url)
    print(f"\nFound subpages: {len(subpages)}\n")

    if not subpages:
        print("No subpages found or an error occurred during crawling.")
        return

    page_structures = {}
    for url in subpages:
        print(f"Processing: {url}")
        page_title, headings = get_headings(url)
        page_structures[url] = {
            'title': page_title,
            'headings': headings,
            'error_flags': []  # Initialize a list to track errors
        }
        print(f"Collected heading structure for '{page_title}'.\n")
    
    # Build error flags for each page
    for url, data in page_structures.items():
        headings = data['headings']
        if not headings:
            # No headings found; depending on requirements, this might be considered an error
            # Here, we choose not to flag it as an error
            continue
        # Build the heading tree and check for errors
        tree = build_tree(headings)
        errors_found = []
        # Check for structural errors
        stack = [0]  # Stack to track heading levels
        for level, title in headings:
            if level > stack[-1] + 1:
                # This is a structural error
                errors_found.append(True)
                break
            while stack and level <= stack[-1]:
                stack.pop()
            stack.append(level)
        
        data['error_flags'] = errors_found

    # Generate the combined HTML document
    generate_combined_html(combined_html_path, page_structures)
    print(f"The combined HTML document has been successfully created: '{combined_html_path}'\n")
    print("All subpages have been processed.")

if __name__ == "__main__":
    main()