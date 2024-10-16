# HeadingCrawler: Website Heading Structure Analyzer

This repository contains **HeadingCrawler**, a Python-based tool designed to crawl websites and analyze their heading structures. By extracting and evaluating the hierarchy of headings (h1 to h6) across all internal pages, HeadingCrawler helps developers and SEO specialists ensure that websites maintain a logical and SEO-friendly structure.

## Purpose

While building or auditing a website, especially for SEO purposes, it's crucial to have a well-organized heading structure. Proper use of headings enhances readability, accessibility, and search engine optimization. However, manually checking the heading hierarchy across multiple pages can be time-consuming and error-prone. **HeadingCrawler** automates this process, providing a comprehensive overview of a website's heading structure and highlighting any inconsistencies or structural issues.

### Key Problems HeadingCrawler Addresses:

- **Inconsistent Heading Hierarchy:** Websites may have improper use of heading levels, such as skipping levels or misusing headings for styling purposes, which can confuse both users and search engines.
- **Time-Consuming Manual Audits:** Manually reviewing each page's heading structure is inefficient, especially for large websites with numerous pages.
- **Lack of Automated Reporting:** Without automated tools, identifying and documenting heading structure issues can be challenging.

### How HeadingCrawler Solves These Problems:

- **Automated Crawling:** Efficiently crawls a website, respecting `robots.txt` directives, to gather all internal subpage URLs.
- **Heading Extraction:** Extracts all heading tags (h1 to h6) from each page, building a hierarchical tree to represent the structure.
- **Structural Analysis:** Evaluates the correctness of heading sequences, identifying any structural errors such as skipped heading levels.
- **Comprehensive Reporting:** Generates a combined HTML report with interactive sections for each subpage's heading structure and a summary report highlighting pages with structural issues.

## Features

- **Robust Web Crawling:** Navigates through internal links up to a specified depth and page limit, ensuring comprehensive coverage of the website.
- **Heading Structure Analysis:** Extracts and organizes headings into a hierarchical tree, making it easy to visualize the structure.
- **Error Detection:** Identifies structural issues in heading usage, such as improper nesting or skipped levels.
- **Automated HTML Report:** Produces a user-friendly HTML document with interactive buttons to view individual page structures and a summary report.
- **Respect for Web Standards:** Adheres to `robots.txt` rules and includes polite crawling delays to minimize server load.

## Installation and Setup

### Prerequisites

- **Python 3.6 or higher**: Ensure you have Python installed on your system. You can download it from [python.org](https://www.python.org/downloads/).

### Dependencies

HeadingCrawler relies on several Python libraries. You can install them using `pip`:

```bash
pip install -r requirements.txt
pip install requests beautifulsoup4 certifi 

git clone https://github.com/yourusername/headingcrawler.git
cd headingcrawler
```

## Typical Use Cases

- **SEO Audits:** Ensure that a website's heading structure is optimized for search engines, enhancing SEO performance.
- **Website Development:** Validate the logical organization of content during the development phase to improve user experience and accessibility.
- **Content Management:** Review and maintain consistent heading usage across large websites with numerous pages.

## Output Report

The generated `heading_structures.html` includes:

- **Interactive Buttons:** Clickable buttons for each subpage to view its heading structure.
- **Heading Hierarchy Visualization:** Display of headings with indentation representing their levels and color-coded indicators for structural correctness.
- **Summary Report:** A dedicated section summarizing pages with heading structure errors for easy reference.

## Future Development

As the primary developer of HeadingCrawler, I plan to continue enhancing its capabilities by:

- **Adding More Analysis Features:** Incorporating checks for accessibility compliance and SEO best practices.
- **Improving Performance:** Optimizing the crawling and analysis process for faster execution on larger websites.
- **Expanding Reporting Options:** Offering different report formats and more detailed analytics.
- **User Interface Enhancements:** Developing a graphical user interface (GUI) for easier interaction and configuration.

Feedback, suggestions, and contributions are highly welcome to help improve HeadingCrawler and make it a more robust tool for web analysis.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your improvements or bug fixes.

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For any inquiries or feedback, please open an issue on the [GitHub repository](https://github.com/DeanBeanBEER-WARE/tag_crawler?tab=readme-ov-file) or contact me at [denniswiebler@gmail.com](mailto:denniswiebler@gmail.com).
