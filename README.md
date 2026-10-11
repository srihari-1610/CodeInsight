# \# 🧠 CodeInsight — AI Code Explainer for Competitive Programmers

# 

# CodeInsight is an AI-powered code analysis and explanation platform built with Python, Streamlit, and the Google Gemini API.

# 

# Paste a Python, C++, or Java solution to receive a line-by-line explanation, time and space complexity analysis, a constraint-aware Time Limit Exceeded (TLE) risk estimate, optimization suggestions, and potential programming pitfalls.

# 

# The application provides a Demo Mode for exploring built-in examples and a Live Mode for analyzing code using the configured Gemini API.

# 

# \## 🚀 Key Features

# 

# | Feature | Description |

# |---|---|

# | AI-Powered Code Explanation | Generates explanations to help users understand programming logic. |

# | Line-by-Line Analysis | Explains source code in a structured, readable format. |

# | Complexity Analysis | Provides time and space complexity estimates with supporting reasoning. |

# | Constraint-Aware TLE Estimation | Evaluates an operation-count formula against user-defined constraints and an estimated execution budget. |

# | Static Code Analysis | Uses Python AST analysis and brace-scanning heuristics for C++ and Java to identify selected code patterns. |

# | Structured AI Output | Uses structured response handling to organize analysis results. |

# | Demo Mode | Provides built-in examples and predefined analyses without requiring a live API request. |

# | Live Mode | Uses the configured Google Gemini API to analyze custom code when valid API credentials are available. |

# | History and Caching | Uses SQLite to store analysis history and reuse cached results where supported. |

# | Report Export | Supports exporting analysis reports in Markdown or JSON format. |

# 

# \*\*Important:\*\* AI-generated explanations, complexity estimates, optimization suggestions, and TLE predictions are estimates. They are not guaranteed to be correct.

# 

# \## 🎯 Project Objectives

# 

# \- Make programming solutions easier to understand.

# \- Help students learn algorithms and problem-solving techniques.

# \- Explain the reasoning behind time and space complexity.

# \- Identify potential performance bottlenecks.

# \- Provide practical optimization suggestions.

# \- Demonstrate the application of generative AI in programming education.

# 

# \## 🛠️ Technology Stack

# 

# | Component | Technology |

# |---|---|

# | Programming Language | Python |

# | User Interface | Streamlit |

# | AI Integration | Google Gemini API |

# | AI SDK | Google Gen AI SDK (`google-genai`), if used by the current implementation |

# | Static Analysis | Python AST and custom source-code heuristics |

# | Data Storage | SQLite |

# | Visualization | Altair, where applicable |

# | Testing | pytest |

# | Version Control | Git and GitHub |

# 

# \## ⚙️ Application Modes

# 

# \### 1. Demo Mode

# 

# Demo Mode allows users to explore the application using predefined examples and analysis results.

# 

# \- Does not require a live Gemini API request for the bundled examples.

# \- Helps users understand the interface and available analysis features.

# \- Works offline if all required application resources are available locally.

# \- Is limited to the examples supported by the current implementation.

# 

# \### 2. Live Mode

# 

# Live Mode enables AI-assisted analysis of user-provided code through the configured Google Gemini API.

# 

# \- Accepts supported source-code input.

# \- Sends analysis requests to the configured Gemini model.

# \- Processes the returned response for presentation in the application.

# \- May require an internet connection and a valid Gemini API key.

# \- Is subject to API availability, model access, rate limits, and applicable usage costs.

# 

# \## 🏗️ System Architecture

# 

# The following diagram describes the intended processing flow. The exact implementation should be verified against the source code.

# 

# ```text

# &#x20;                 User

# &#x20;                  |

# &#x20;                  v

# &#x20;           Streamlit UI

# &#x20;              app.py

# &#x20;                  |

# &#x20;                  v

# &#x20;         Input Validation

# &#x20;            validators.py

# &#x20;                  |

# &#x20;                  v

# &#x20;         Analysis Controller

# &#x20;            analyzer.py

# &#x20;                  |

# &#x20;                  v

# &#x20;           History / Cache

# &#x20;            history.py

# &#x20;                  |

# &#x20;         +--------+--------+

# &#x20;         |                 |

# &#x20;      Cache Hit          Cache Miss

# &#x20;         |                 |

# &#x20;         v                 v

# &#x20;    Cached Result       Prompt Builder

# &#x20;                         prompts.py

# &#x20;                             |

# &#x20;                             v

# &#x20;                      AI Integration

# &#x20;                          llm.py

# &#x20;                             |

# &#x20;                   +---------+---------+

# &#x20;                   |                   |

# &#x20;                Live Mode           Demo Mode

# &#x20;                   |                   |

# &#x20;                   v                   v

# &#x20;              Gemini API        Built-in Samples

# &#x20;                   |                   |

# &#x20;                   +---------+---------+

# &#x20;                             |

# &#x20;                             v

# &#x20;                     Response Processing

# &#x20;                         schemas.py

# &#x20;                             |

# &#x20;                             v

# &#x20;                   Complexity and Static

# &#x20;                        Analysis

# &#x20;                             |

# &#x20;                             v

# &#x20;                     Results Interface

# &#x20;                             |

# &#x20;             +---------------+---------------+

# &#x20;             |               |               |

# &#x20;             v               v               v

# &#x20;         Explanation      TLE Estimate    Optimization

# &#x20;             |

# &#x20;             v

# &#x20;        Report Export

# ```

# 

# \## 📁 Project Structure

# 

# ```text

# CodeInsight/

# |

# |-- app.py

# |-- requirements.txt

# |-- README.md

# |-- .env.example

# |-- .gitignore

# |

# |-- core/

# |   |-- config.py

# |   |-- validators.py

# |   |-- prompts.py

# |   |-- llm.py

# |   |-- schemas.py

# |   |-- analyzer.py

# |   |-- static\_analysis.py

# |   |-- complexity.py

# |   |-- history.py

# |   |-- report.py

# |   |-- samples.py

# |

# |-- tests/

# |

# |-- data/

# ```

# 

# The structure above is representative. Some files or directories may be absent or named differently in your current repository. The actual GitHub project structure is authoritative.

# 

# \## 💻 Installation and Setup

# 

# \### Prerequisites

# 

# \- Python installed on your system.

# \- Git installed on your system.

# \- Internet access for installing dependencies and using the live Gemini API.

# \- A Gemini API key for Live Mode, if required by your configuration.

# 

# \### Step 1: Clone the Repository

# 

# ```bash

# git clone https://github.com/srihari-1610/CodeInsight.git

# cd CodeInsight

# ```

# 

# \### Step 2: Create a Virtual Environment

# 

# ```bash

# python -m venv .venv

# ```

# 

# \### Step 3: Activate the Environment

# 

# \*\*Windows Command Prompt:\*\*

# 

# ```cmd

# .venv\\Scripts\\activate

# ```

# 

# \*\*Windows PowerShell:\*\*

# 

# ```powershell

# .\\.venv\\Scripts\\Activate.ps1

# ```

# 

# \*\*Linux or macOS:\*\*

# 

# ```bash

# source .venv/bin/activate

# ```

# 

# \### Step 4: Install Dependencies

# 

# ```bash

# python -m pip install --upgrade pip

# pip install -r requirements.txt

# ```

# 

# \### Step 5: Configure the Gemini API

# 

# The application uses the configuration supported by `core/config.py`.

# 

# If the application expects `GEMINI\_API\_KEY` as an environment variable, create a local `.env` file using the example configuration:

# 

# ```text

# GEMINI\_API\_KEY=your\_gemini\_api\_key\_here

# ```

# 

# Replace the placeholder with your own key in your local environment.

# 

# Never publish a real API key to GitHub.

# 

# If the application uses Streamlit secrets instead of loading `.env` directly, configure the key through the supported secrets mechanism.

# 

# \### Step 6: Run the Application

# 

# ```bash

# streamlit run app.py

# ```

# 

# Open the local address printed in the terminal.

# 

# \## 🧪 Testing

# 

# Run the project's automated tests with:

# 

# ```bash

# python -m pytest -q

# ```

# 

# The tests should be used to verify components such as:

# 

# \- Input validation.

# \- Code-analysis processing.

# \- Structured response handling.

# \- Complexity evaluation.

# \- Caching and history.

# \- Demo Mode.

# \- Live API integration using suitable mocks or test credentials.

# 

# The actual test results depend on the current code and environment. Only report a test count or successful result after verifying it.

# 

# \## 🔐 Security Considerations

# 

# \- API keys must be kept private.

# \- Environment files containing credentials must not be committed.

# \- User-submitted source code should be treated as untrusted input.

# \- AI-generated output should be validated before being processed or displayed.

# \- Complexity expressions should be evaluated using restricted, safe logic.

# \- Do not execute user-submitted code unless a separate, appropriately isolated execution environment has been implemented.

# 

# CodeInsight is intended to analyze source code as text. Verify the implementation before making claims about execution or sandboxing.

# 

# \## ⚠️ Limitations

# 

# \- AI-generated explanations and complexity estimates may be incorrect.

# \- Static-analysis heuristics cannot identify every algorithmic pattern.

# \- TLE estimates use an approximate operations-per-second budget rather than actual benchmarking.

# \- Live Mode depends on the configured AI provider and API availability.

# \- Demo Mode is limited to its bundled examples.

# \- Supported programming languages and input limits depend on the implementation.

# \- Large or complex source files may exceed application or model limits.

# 

# \## 🔮 Future Enhancements

# 

# \- Support additional programming languages.

# \- Improve complexity estimation and performance analysis.

# \- Add benchmark-based runtime comparisons.

# \- Support importing competitive programming problem statements.

# \- Add isolated sample-test execution where safely implemented.

# \- Improve visualization of algorithmic complexity.

# \- Enhance test coverage and error handling.

# \- Explore additional AI models and analysis techniques.

# 

# \## 📚 References

# 

# \- Python Documentation: https://docs.python.org/3/

# \- Streamlit Documentation: https://docs.streamlit.io/

# \- Google Gemini API Documentation: https://ai.google.dev/gemini-api/docs

# \- Google Gen AI Python SDK: https://github.com/googleapis/python-genai

# \- pytest Documentation: https://docs.pytest.org/

# 

# \## 👨‍💻 Author

# 

# \*\*SRIHARI PEDDAPURAM\*\*

# 

# GitHub Repository: https://github.com/srihari-1610/CodeInsight

# 

# \---

# 

# \*CodeInsight — Making competitive programming solutions easier to understand.\*

