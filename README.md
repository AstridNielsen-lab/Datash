# Datash - Data + Shell + Intelligence

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> An intelligent terminal assistant for programmers to interact with databases, process data, and automate tasks.

## 🌟 Overview

Datash is a powerful terminal-based assistant that helps programmers interact with databases, manipulate data, execute shell commands, and manage Git repositories - all with intelligent suggestions and autocompletion powered by Google's Gemini API.

![image](https://github.com/user-attachments/assets/4e084d77-c059-4260-83c8-426ccbea485e)
![image](https://github.com/user-attachments/assets/b631ddd4-b9c8-41ac-a489-a82c3cf187e7)
![image](https://github.com/user-attachments/assets/ba8ece11-7c4c-4418-9de2-fb7357b12183)
![image](https://github.com/user-attachments/assets/ad965cc0-b3b4-4ea4-8914-27e36220dd5e)



## ✨ Features

- **Natural Language Processing**: Interact with your terminal using plain English commands
- **Intelligent Autocompletion**: Get smart suggestions based on context
- **Database Operations**: Connect to and work with MySQL, PostgreSQL, SQLite, MongoDB, and more
- **Code Generation**: Generate code snippets for data manipulation, queries, and automation
- **Shell Integration**: Execute and get help with Bash/PowerShell commands
- **Git Support**: Simplify common Git operations with natural language
- **Data Processing**: Import, transform, and analyze data from various formats
- **Zero Data Retention**: Your data stays on your machine, ensuring privacy
- **Secure Data Transfer**: Encrypted data sharing between systems
- **Cross-Platform Support**: Compatible with Windows, macOS, and Linux

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A Gemini API key from [Google AI Studio](https://ai.google.dev/)

### Option 1: Install from PyPI (Recommended)

```bash
# Install Datash using pip
pip install datash

# Verify installation
datash --version
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/juliocamposmachado/datash.git
cd datash

# Install dependencies
pip install -r requirements.txt

# Run directly
python main.py
```

### Platform-Specific Notes

#### Windows

On Windows, Datash uses `pyreadline3` for command history and autocompletion. This is automatically installed with the dependencies.

```powershell
# Run with PowerShell
python main.py
```

#### Linux/macOS

The `readline` package is used on Unix-based systems for similar functionality.

```bash
# Run on Linux/macOS
python main.py
```

### Executable Version

A pre-built Windows executable will be available in the `dist` folder of the repository in future releases.

## ⚙️ Configuration

### API Key Setup

1. Obtain a Gemini API key from [Google AI Studio](https://ai.google.dev/)
2. Set up your API key using one of these methods:

   a. Create a `.env` file in the Datash directory:
   ```
   DATASH_API_KEY=your_gemini_api_key_here
   ```

   b. Set an environment variable:
   ```bash
   # Linux/macOS
   export DATASH_API_KEY=your_gemini_api_key_here
   
   # Windows (PowerShell)
   $env:DATASH_API_KEY="your_gemini_api_key_here"
   ```

   c. Provide it at runtime (not recommended for regular use):
   ```bash
   DATASH_API_KEY=your_key python main.py
   ```

### Configuration File

Datash creates a configuration file at `~/.datash_config.json` when you first run the application. You can modify settings by:

1. Using the built-in commands: `!config set key value`
2. Directly editing the configuration file

Available configuration options:

| Setting | Description | Default |
|---------|-------------|---------|
| `api_url` | Gemini API endpoint URL | `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent` |
| `history_file` | Path to command history file | `~/.datash_history` |
| `max_history` | Maximum number of history entries | `100` |
| `display_suggestions` | Show suggestions after commands | `true` |

## 🔍 Usage Examples

### Basic Interaction

```
datash> How do I connect to a PostgreSQL database in Python?
```

Response:
```python
import psycopg2

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="mydatabase",
    user="myuser",
    password="mypassword",
    port="5432"
)

# Create a cursor
cursor = conn.cursor()

# Execute a query
cursor.execute("SELECT * FROM mytable")

# Fetch results
results = cursor.fetchall()

# Close connection
cursor.close()
conn.close()
```

### Data Import Example

```
datash> import csv to sqlite and create a table
```

Response:
```python
import sqlite3
import csv

# Connect to SQLite database (creates it if it doesn't exist)
conn = sqlite3.connect('my_database.db')
cursor = conn.cursor()

# Create table (adjust column names and types as needed)
cursor.execute('''
CREATE TABLE IF NOT EXISTS my_table (
    id INTEGER PRIMARY KEY,
    name TEXT,
    age INTEGER,
    email TEXT
)
''')

# Import CSV data
with open('data.csv', 'r') as csv_file:
    csv_reader = csv.reader(csv_file)
    header = next(csv_reader)  # Skip header row
    
    for row in csv_reader:
        cursor.execute('''
        INSERT INTO my_table (id, name, age, email)
        VALUES (?, ?, ?, ?)
        ''', row)

# Commit changes and close connection
conn.commit()
conn.close()
```

### Direct Shell Command Execution

```
datash> $ ls -la
```

Response:
```
total 52
drwxr-xr-x 1 user group   4096 Jun 02 18:30 .
drwxr-xr-x 1 user group   4096 Jun 02 18:00 ..
-rw-r--r-- 1 user group    220 Jun 02 18:00 .env.example
-rw-r--r-- 1 user group  22152 Jun 02 18:30 main.py
-rw-r--r-- 1 user group   1794 Jun 02 18:10 requirements.txt
```

### Git Operations

```
datash> how do I squash my last 3 commits
```

Response:
```bash
# To squash your last 3 commits into one:
git reset --soft HEAD~3
git commit -m "Your new commit message"

# If you've already pushed to remote:
git push --force  # Be careful with this!
```

## 📋 Command Reference

### Built-in Commands

| Command | Description |
|---------|-------------|
| `!help` | Display help information |
| `!exit`, `!quit` | Exit the application |
| `!clear` | Clear the terminal screen |
| `!config` | Show current configuration |
| `!config set KEY VALUE` | Update configuration |
| `!version` | Show version information |
| `!history` | Show command history |

### Special Syntax

| Syntax | Description |
|--------|-------------|
| `$ command` | Execute shell command directly |

## 📦 Dependencies

Datash relies on the following main packages:

- `requests`: For API communication with Gemini
- `python-dotenv`: For environment variable management
- `colorama`: For colored terminal output
- `readline`/`pyreadline3`: For command history and editing
- Various database connectors (optional): For database interactions

For a complete list of dependencies, see the [requirements.txt](requirements.txt) file.

## 🗺️ Development Roadmap

| Version | Platform | Features | Target Date |
|---------|----------|----------|-------------|
| 1.0.0   | Desktop (Windows/macOS/Linux) | Core functionality, API client, database utilities | June 2025 |
| 1.1.0   | Desktop | Enhanced UI, performance improvements | July 2025 |
| 1.5.0   | Android | Mobile interface, offline functionality | September 2025 |
| 1.6.0   | iOS | Mobile interface, iOS-specific optimizations | November 2025 |
| 2.0.0   | All platforms | Cross-device synchronization, cloud integration | January 2026 |

### Development Status

- **Desktop Version**: ✅ Initial release available
- **Android Version**: 🔄 Planned for Q3 2025
- **iOS Version**: 🔄 Planned for Q4 2025

## 🤝 Contributing

Contributions are welcome! Here's how you can contribute:

1. **Fork the repository**
2. **Create a new branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Add tests** for new functionality
5. **Run tests**: `pytest`
6. **Commit your changes**: `git commit -m "Add your feature"`
7. **Push to the branch**: `git push origin feature/your-feature-name`
8. **Submit a pull request**

Please make sure your code follows the project's coding style and includes appropriate tests.

### 💰 Financial Contributions

Your donations help educate new developers in technology!

- **PIX/PayPal**: radiotatuapefm@gmail.com
- **Bitcoin**: bc1qmjf00jqttk2kgemxtxh0hv4xp8fqztnn23cuc2
- **Ethereum**: 0x7481B4591e7f0DFAD23b884E78C46F0c207a3E35
- **Litecoin**: ltc1qxytts52mykr2u83x6ghwllmu7d524ltt702mcc

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Founder & CTO

**Julio Campos Machado**  
Full Stack Developer & CTO at Like Look Solutions

### Contact Information
- **WhatsApp**: +55 11 97060-3441
- **Email**: juliocamposmachado@gmail.com
- **LinkedIn**: [juliocamposmachado](https://www.linkedin.com/in/juliocamposmachado/)
- **Linktree**: [juliocamposmachado](https://linktr.ee/juliocamposmachado)

### Company
- **Like Look Solutions**
- **Website**: [https://likelook.wixsite.com/solutions](https://likelook.wixsite.com/solutions)
- **Facebook**: [likelooksolutionsti](https://www.facebook.com/likelooksolutionsti/)

## 🙏 Acknowledgements

- Google's Gemini API for powering the AI capabilities
- The open source community for the amazing libraries that make this project possible

---

<p align="center">
  Made with ❤️ by the Datash team
</p>
