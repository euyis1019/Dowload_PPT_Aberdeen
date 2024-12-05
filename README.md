# Aberdeen Course Review Assistant

## Project Overview

The **Aberdeen Course Review Assistant** is an automated tool designed to enhance the reviewing experience for Aberdeen University courses. It streamlines the process of downloading, organizing, and analyzing course materials, while leveraging **LLM** (Large Language Models) to provide accurate and well-sourced responses based on course-related queries.

### Basic Workflow

1. **Automated Download**
    
    - The process begins by automatically downloading course materials, including **PPTs**, **assessments**, and **practice materials**.
    - These files are then organized into a structured directory for easy access.
2. **PDF to Markdown Conversion**
    
    - After downloading, the system converts **PDF files** into **Markdown format**.
    - This conversion enhances the accessibility and integration of the content, making it easier to work with in the AI-powered knowledge base.
3. **AI-Powered Knowledge Base**
    
    - Once the materials are processed, they are incorporated into an **AI-powered knowledge base**.
    - Using **RAG (Retrieval-Augmented Generation)**, the system enhances the accuracy of AI-generated responses by referring to the knowledge base, ensuring proper source attribution.

## Installation

### Prerequisites

- Python 3.x
- Chrome/Chromium browser (required for DrissionPage automation)

### Required Dependencies

You can install the required dependencies using `pip`:

```bash
pip install -r requirements.txt
```

The [`requirements.txt`](requirements.txt) file includes the following key libraries:

```txt
DrissionPage==0.5.0
tqdm==4.66.1
retrying==1.3.3
```

### Getting Started

1. **Clone the Repository**: First, clone the repository to your local machine:
    
    ```bash
    git clone [repository-url]
    cd aberdeen-course-review
    ```
    
2. **Install the Dependencies**: Install the required Python libraries:
    
    ```bash
    pip install -r requirements.txt
    ```
    
3. **Configure Parameters**: Open the script file [`main.py`](main.py) or [`main_v2.py`](main_v2_LanguagesAndComputability.py) and update the relevant parameters for your course materials.
    

**Note**: The [folder_tree]([https://github.com/your-username/another-repository](https://github.com/euyis1019/folder_treeForLLM))
tool, although included, is not central to the main project functionality. It is used to customarily generate clear project folder structure.

### Contribution and Record

- **Update the `README.md`** whenever you make significant changes or add new features.
- **Share any useful tools or knowledge** you learn during development in WeChat or in the [`log.md`](log.md).
- **Document useful tools and techniques** you discover during development, or anything else you think is worth recording in [`log.md`](log.md) (please follow the format).
