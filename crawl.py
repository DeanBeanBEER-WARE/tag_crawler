import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import re
from collections import deque

class HeadingNode:
    """
    Class representing a node in the headings tree.

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
        Adds a child node to the current heading.

        Args:
            child (HeadingNode): The child node to be added.
        """
        self.children.append(child)

def get_headings(url):
    """
    Extracts all headings (h1 to h6) from the specified URL.

    The headings are collected in the order they appear on the webpage and
    returned as a list of tuples (level, title).

    Args:
        url (str): The URL of the webpage from which to extract headings.

    Returns:
        list: A list of tuples, each containing the heading level and title.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; HeadingCrawler/1.0; +http://yourdomain.com/crawler)'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Check if the request was successful
    except requests.RequestException as e:
        print(f"Error fetching the URL '{url}': {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')

    headings = []
    # Search for all heading tags h1 to h6 in the order they appear
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        level = int(tag.name[1])  # Extract level from tag name, e.g., h2 -> 2
        title = tag.get_text(strip=True)  # Extract text without leading/trailing whitespace
        headings.append((level, title))
    
    return headings

def build_tree(headings):
    """
    Builds a hierarchical tree from the list of headings.

    Each heading is placed as a child of the previous heading with a lower level.

    Args:
        headings (list): A list of tuples (level, title) of the headings.

    Returns:
        HeadingNode: The root node of the constructed headings tree.
    """
    root = HeadingNode(0, "Root")  # Virtual root node with level 0
    stack = [root]  # Stack to keep track of the current path in the tree

    for level, title in headings:
        node = HeadingNode(level, title)  # Create a new node for the heading
        
        # Find the appropriate parent node by traversing the stack
        while stack and stack[-1].level >= level:
            stack.pop()  # Remove nodes from the stack that have a higher or equal level
        
        # The current node is a child of the last node in the stack
        stack[-1].add_child(node)
        stack.append(node)  # Add the current node to the stack
    
    return root

def sanitize_filename(url):
    """
    Generates a safe filename from a URL by replacing non-alphanumeric characters.

    Args:
        url (str): The URL to be converted into a filename.

    Returns:
        str: A sanitized filename.
    """
    parsed_url = urlparse(url)
    path = parsed_url.path.strip('/')
    if not path:
        path = 'home'
    filename = re.sub(r'[^a-zA-Z0-9_-]', '_', path)
    return f"{filename}.txt"

def print_tree(node, file, indent=0):
    """
    Recursively writes the headings tree to a file with appropriate indentation.

    Each heading line starts with its tag (e.g., h1 - , h2 - ) followed by the title.

    Args:
        node (HeadingNode): The current node in the tree.
        file (file object): The open file object to write to.
        indent (int, optional): The current indentation level. Defaults to 0.
    """
    if node.level != 0:  # Skip the virtual root node
        # Write the heading with corresponding indentation and its tag
        file.write('  ' * indent + f'h{node.level} - {node.title}\n')
    for child in node.children:
        print_tree(child, file, indent + 1)  # Recursive call for child nodes

def is_internal_link(link, base_domain):
    """
    Determines if a link is internal (i.e., belongs to the same domain).

    Args:
        link (str): The URL to check.
        base_domain (str): The base domain to compare against.

    Returns:
        bool: True if the link is internal, False otherwise.
    """
    parsed_link = urlparse(link)
    return (parsed_link.netloc == base_domain) or (parsed_link.netloc == '')

def crawl_website(base_url):
    """
    Crawls the website starting from the base URL and collects all internal subpage URLs.

    Args:
        base_url (str): The main domain URL to start crawling from.

    Returns:
        set: A set of unique internal subpage URLs.
    """
    visited = set()  # Set to keep track of visited URLs
    queue = deque()  # Queue for BFS traversal
    queue.append(base_url)
    visited.add(base_url)

    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    while queue:
        current_url = queue.popleft()
        print(f"Crawling: {current_url}")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; HeadingCrawler/1.0; +http://yourdomain.com/crawler)'
            }
            response = requests.get(current_url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to retrieve '{current_url}': {e}")
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
                    visited.add(normalized_href)
                    queue.append(normalized_href)

    return visited

def create_output_directory(base_url):
    """
    Creates an output directory named after the main domain.

    Args:
        base_url (str): The main domain URL.

    Returns:
        str: The path to the created directory.
    """
    parsed_url = urlparse(base_url)
    domain_name = parsed_url.netloc
    # Remove 'www.' prefix if present for cleaner directory name
    if domain_name.startswith('www.'):
        domain_name = domain_name[4:]
    # Define the directory path
    directory_path = os.path.join(os.getcwd(), domain_name)
    # Create the directory if it doesn't exist
    os.makedirs(directory_path, exist_ok=True)
    return directory_path

def main():
    """
    Main function to execute the script.

    It prompts the user for the main domain URL, crawls all internal subpages,
    extracts their headings structure, and writes each structure to separate text files
    within a dedicated directory named after the main domain.
    """
    base_url = input("Enter the main domain URL: ").strip()
    
    # Validate the URL
    parsed_base = urlparse(base_url)
    if not parsed_base.scheme or not parsed_base.netloc:
        print("Invalid URL. Please include the scheme (e.g., 'https://').")
        return

    # Create output directory
    output_directory = create_output_directory(base_url)
    print(f"\nHeadings will be saved in the directory: {output_directory}\n")

    print("Starting to crawl the website. This may take a while depending on the size of the site...\n")
    subpages = crawl_website(base_url)
    print(f"\nFound {len(subpages)} subpages.\n")

    if not subpages:
        print("No subpages found or an error occurred during crawling.")
        return

    for url in subpages:
        print(f"Processing: {url}")
        headings = get_headings(url)
        if not headings:
            print(f"No headings found or failed to retrieve headings for '{url}'.\n")
            continue

        tree = build_tree(headings)
        filename = sanitize_filename(url)
        file_path = os.path.join(output_directory, filename)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                print_tree(tree, f)
            print(f"Headings structure saved to '{file_path}'.\n")
        except IOError as e:
            print(f"Error writing to file '{file_path}': {e}\n")

    print("All subpages have been processed.")

if __name__ == "__main__":
    main()