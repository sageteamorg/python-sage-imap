.. _contributing:

Contributing Guide
==================

We welcome contributions to Python Sage IMAP! This guide will help you get started with contributing to the project.

Getting Started
---------------

Types of Contributions
~~~~~~~~~~~~~~~~~~~~~~

We appreciate all types of contributions:

- **Bug reports**: Help us identify and fix issues
- **Feature requests**: Suggest new functionality
- **Code contributions**: Submit bug fixes and new features
- **Documentation**: Improve or add to our documentation
- **Testing**: Help improve our test coverage
- **Examples**: Share how you use the library

How to Contribute
~~~~~~~~~~~~~~~~~

1. **Fork the repository** on GitHub
2. **Create a feature branch** from ``main``
3. **Make your changes** following our guidelines
4. **Test your changes** thoroughly
5. **Submit a pull request** with a clear description

Code of Conduct
~~~~~~~~~~~~~~~

Please note that this project follows a `Code of Conduct <https://github.com/sageteamorg/python-sage-imap/blob/main/CODE_OF_CONDUCT.md>`_. By participating, you are expected to uphold this code.

Development Setup
-----------------

Prerequisites
~~~~~~~~~~~~~

- Python 3.7 or higher
- Git
- A GitHub account

Setting Up Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Fork and clone the repository**:

   .. code-block:: bash

      git clone https://github.com/YOUR_USERNAME/python-sage-imap.git
      cd python-sage-imap

2. **Create a virtual environment**:

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # On Windows: venv\Scripts\activate

3. **Install the package in development mode**:

   .. code-block:: bash

      pip install -e ".[dev]"

4. **Install pre-commit hooks** (optional but recommended):

   .. code-block:: bash

      pre-commit install

5. **Verify the setup**:

   .. code-block:: bash

      pytest --version
      python -c "import sage_imap; print('Setup successful!')"

Development Workflow
~~~~~~~~~~~~~~~~~~~~

1. **Create a feature branch**:

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. **Make your changes** following the coding standards
3. **Run tests** to ensure nothing is broken
4. **Update documentation** if needed
5. **Commit your changes** with a clear message
6. **Push to your fork** and create a pull request

Coding Standards
----------------

Code Style
~~~~~~~~~~

We follow PEP 8 with some additional conventions:

- **Line length**: Maximum 88 characters (Black formatter default)
- **Import organization**: Use ``isort`` to organize imports
- **Docstrings**: Follow Google/NumPy style (see examples below)
- **Type hints**: Use type hints for all public APIs
- **Variable names**: Use descriptive names, avoid abbreviations

Code Formatting
~~~~~~~~~~~~~~~

We use automated tools to maintain consistent code style:

.. code-block:: bash

   # Format code with Black
   black sage_imap tests
   
   # Sort imports with isort
   isort sage_imap tests
   
   # Check with flake8
   flake8 sage_imap tests

These tools are configured in ``pyproject.toml`` and will run automatically if you install pre-commit hooks.

Docstring Style
~~~~~~~~~~~~~~~

Use Google-style docstrings:

.. code-block:: python

   def search_messages(self, criteria: IMAPSearchCriteria) -> List[Message]:
       """Search for messages matching the given criteria.
       
       Args:
           criteria (IMAPSearchCriteria): Search criteria to apply.
           
       Returns:
           List[Message]: List of messages matching the criteria.
           
       Raises:
           IMAPSearchError: If the search operation fails.
           IMAPConnectionError: If the connection is lost.
           
       Example:
           >>> criteria = IMAPSearchCriteria().from_address("sender@example.com")
           >>> messages = mailbox.search(criteria)
           >>> print(f"Found {len(messages)} messages")
           
       Note:
           This method uses server-side search capabilities for efficiency.
       """
       pass

Type Hints
~~~~~~~~~~

Use type hints for better code documentation and IDE support:

.. code-block:: python

   from typing import List, Optional, Union, Dict, Any
   
   def process_messages(
       messages: List[Message],
       batch_size: int = 100,
       callback: Optional[Callable[[Message], None]] = None
   ) -> Dict[str, Any]:
       """Process messages in batches."""
       pass

Testing
-------

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   pytest
   
   # Run with coverage
   pytest --cov=sage_imap
   
   # Run specific test file
   pytest tests/test_client.py
   
   # Run specific test
   pytest tests/test_client.py::TestIMAPClient::test_connection

Writing Tests
~~~~~~~~~~~~~

We use ``pytest`` for testing. Follow these guidelines:

1. **Test file naming**: ``test_*.py`` or ``*_test.py``
2. **Test function naming**: ``test_<functionality>``
3. **Test class naming**: ``Test<ClassName>``
4. **Use fixtures**: For common setup/teardown
5. **Mock external dependencies**: Use ``unittest.mock`` or ``pytest-mock``

Example test:

.. code-block:: python

   import pytest
   from unittest.mock import Mock, patch
   from sage_imap.services import IMAPClient
   from sage_imap.exceptions import IMAPConnectionError
   
   
   class TestIMAPClient:
       """Test cases for IMAPClient."""
       
       def test_connection_success(self):
           """Test successful connection."""
           client = IMAPClient(
               host="imap.example.com",
               username="user",
               password="pass"
           )
           
           with patch('imaplib.IMAP4_SSL') as mock_imap:
               mock_imap.return_value.login.return_value = ('OK', [])
               
               client.connect()
               
               mock_imap.assert_called_once()
               mock_imap.return_value.login.assert_called_once_with("user", "pass")
       
       def test_connection_failure(self):
           """Test connection failure handling."""
           client = IMAPClient(
               host="invalid.example.com",
               username="user",
               password="pass"
           )
           
           with patch('imaplib.IMAP4_SSL') as mock_imap:
               mock_imap.side_effect = OSError("Connection failed")
               
               with pytest.raises(IMAPConnectionError):
                   client.connect()

Test Coverage
~~~~~~~~~~~~~

We aim for high test coverage. Check coverage with:

.. code-block:: bash

   pytest --cov=sage_imap --cov-report=html
   
   # Open coverage report
   open htmlcov/index.html

Guidelines for good test coverage:

- Test both success and failure scenarios
- Test edge cases and boundary conditions
- Mock external dependencies (IMAP servers)
- Test error handling and exceptions
- Include integration tests for key workflows

Documentation
-------------

Documentation Structure
~~~~~~~~~~~~~~~~~~~~~~~

Our documentation is built with Sphinx and includes:

- **API Reference**: Auto-generated from docstrings
- **User Guide**: Getting started and usage examples
- **Examples**: Complete working examples
- **FAQ**: Common questions and solutions
- **Troubleshooting**: Solutions to common issues

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Navigate to docs directory
   cd docs
   
   # Build documentation
   make html
   
   # On Windows
   make.bat html
   
   # Open in browser
   open _build/html/index.html

Writing Documentation
~~~~~~~~~~~~~~~~~~~~~

1. **Use reStructuredText** (``.rst`` files)
2. **Follow consistent formatting**:

   - Use ``=`` for main headings
   - Use ``-`` for section headings
   - Use ``~`` for subsection headings
   - Use ``^`` for sub-subsection headings

3. **Include code examples**:

   .. code-block:: python

      from sage_imap.services import IMAPClient
      
      # Always include working examples
      client = IMAPClient(host="imap.gmail.com", username="user", password="pass")

4. **Cross-reference** other parts of the documentation:

   .. code-block:: rst

      See :ref:`api_reference` for complete API documentation.
      
      Link to classes: :class:`sage_imap.services.client.IMAPClient`
      
      Link to functions: :func:`sage_imap.services.client.IMAPClient.connect`

5. **Use admonitions** for important information:

   .. code-block:: rst

      .. note::
         This is a note for additional information.
      
      .. warning::
         This is a warning about potential issues.
      
      .. tip::
         This is a helpful tip for users.

API Documentation
~~~~~~~~~~~~~~~~~

API documentation is auto-generated from docstrings. Ensure your docstrings are complete and follow the Google style.

Pull Request Process
--------------------

Creating a Pull Request
~~~~~~~~~~~~~~~~~~~~~~~

1. **Ensure your branch is up to date**:

   .. code-block:: bash

      git checkout main
      git pull upstream main
      git checkout your-feature-branch
      git rebase main

2. **Run all tests and checks**:

   .. code-block:: bash

      pytest
      black sage_imap tests
      isort sage_imap tests
      flake8 sage_imap tests

3. **Create a clear commit message**:

   .. code-block:: bash

      git commit -m "Add feature: brief description
      
      - Detailed explanation of changes
      - Why this change was necessary
      - Any breaking changes or migration notes"

4. **Push to your fork**:

   .. code-block:: bash

      git push origin your-feature-branch

5. **Create the pull request** on GitHub

Pull Request Guidelines
~~~~~~~~~~~~~~~~~~~~~~~

**Title**: Use a clear, descriptive title

**Description**: Include:

- **What**: Brief description of the change
- **Why**: Explanation of the motivation
- **How**: Overview of the implementation approach
- **Testing**: Description of how you tested the changes
- **Breaking changes**: Any backward-incompatible changes

**Template**:

.. code-block:: text

   ## Description
   Brief description of the change.
   
   ## Motivation
   Why is this change needed?
   
   ## Changes
   - List of changes made
   - Any breaking changes
   
   ## Testing
   - How you tested the changes
   - Any new tests added
   
   ## Checklist
   - [ ] Tests pass
   - [ ] Documentation updated
   - [ ] Code follows style guidelines
   - [ ] Breaking changes documented

Review Process
~~~~~~~~~~~~~~

1. **Automated checks**: CI will run tests and code quality checks
2. **Code review**: Maintainers will review your code
3. **Feedback**: Address any feedback or requested changes
4. **Approval**: Once approved, your PR will be merged

Be prepared to:

- Answer questions about your implementation
- Make changes based on feedback
- Rebase your branch if needed
- Update documentation or tests

Release Process
---------------

We follow semantic versioning (SemVer):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality, backward compatible
- **PATCH**: Bug fixes, backward compatible

Releases are managed by maintainers and include:

1. Version bump in ``pyproject.toml``
2. Updated ``CHANGELOG.md``
3. Git tag creation
4. PyPI package upload
5. GitHub release with release notes

Community
---------

Communication Channels
~~~~~~~~~~~~~~~~~~~~~~

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Pull Requests**: Code contributions
- **Documentation**: Improvements and additions

Getting Help
~~~~~~~~~~~~

If you need help with contributing:

1. **Check existing issues** and pull requests
2. **Read this contributing guide** thoroughly
3. **Ask in GitHub Discussions** for general questions
4. **Open an issue** for specific problems
5. **Mention maintainers** in your pull request if you need guidance

Recognition
~~~~~~~~~~~

Contributors are recognized in:

- ``CONTRIBUTORS.md`` file
- GitHub contributor statistics
- Release notes for significant contributions
- Special thanks in documentation

Thank you for contributing to Python Sage IMAP! Your contributions help make this library better for everyone. 