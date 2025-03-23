





[<img align="right" src="https://visitor-badge.laobi.icu/badge?page_id=commoncodebase-ccb/safeCodeProvider">
](https://visitor-badge.laobi.icu/badge?page_id=commoncodebase-ccb/safeCodeProvider)



# **Coding Exam Platform**

<p align="center">
  <img src="ccbLogo.png" alt="Project Logo" width="300" align="left">
</p>
<br><br><br><br><br><br><br><br><br>

## **Overview**
The Coding Exam Platform is a specialized local network-based system designed for university-level software and computer engineering students. It provides a structured and secure coding examination environment, similar to online coding challenge platforms like HackerRank, ensuring fairness and efficiency in programming assessments.

## **Key Features**

### **Instructor Capabilities**
- **Exam Setup:**
  - Uploads essential files before the exam:
    - **Assignment File:** Contains problem statements and exam instructions.
    - **Student List File:** Specifies the students participating in the exam.
    - **Pre-prepared Code File:** Includes starter code in the designated programming language (.py, .java, .c, etc.).
  - Configures key exam parameters:
    - **Exam Duration**
    - **Exam Name**
    - **Output Directory:** Defines the location where students' final submissions are stored with their student numbers.
- **Live Monitoring:**
  - Tracks students' progress in real-time.
  - Views the most recent code submissions and execution results of individual students.

### **Student Capabilities**
- **Secure Login:**
  - Authenticates using:
    - **Student Number**
    - **Full Name**
    - **Exam Password** (predefined by the instructor)
- **Coding Environment:**
  - **Left Panel:** Displays the assignment instructions.
  - **Right Panel:** Provides an integrated code editor for real-time programming.
- **Execution Environment:**
  - Runs code within a **Docker container**, dynamically selecting the appropriate compiler/interpreter based on the assigned programming language.
- **Submission System:**
  - Allows students to execute and test their code.
  - Final submissions are securely stored in the instructor-specified directory.

## **Technical Architecture**
- **Backend:** Handles user authentication, exam configuration, and file management.
- **Frontend:** Provides an interactive and intuitive coding interface.
- **Docker Integration:** Ensures an isolated and standardized execution environment for different programming languages.
- **Local Network Deployment:** Operates entirely within the university’s lab infrastructure, ensuring a controlled and secure examination setting without internet dependency.

## **Workflow**
1. The instructor sets up the exam, defining the necessary configurations and uploading required files.
2. Students log in securely using their credentials.
3. The exam interface loads, allowing students to write, execute, and test their code.
4. The instructor monitors students' progress and reviews real-time code execution results.
5. Students submit their final solutions, which are automatically stored in the designated output directory.
6. The exam concludes either upon time expiration or manual termination by the instructor.


### Prerequisites

-   ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white) 
-   ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) 
-   ![Django](https://img.shields.io/badge/Django-092E20?style=flat&logo=django&logoColor=white) 


### Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/commoncodebase-ccb/safeCodeProvider.git
    ```

2.  Install dependencies:

    Python Installation: [Download Python](https://www.python.org/downloads/)

    Django Installation: [Download Django](https://www.djangoproject.com/download/)

    Docker Installation: [Download Docker](https://docs.docker.com/desktop/)


4.  Run the application:

   ```bash
   cd .\safeCodeProvider\
  ```
  ```bash
   py manage.py runserver 8000 --settings=safeCodeProvider.settings.teacher_settings
  ```

## **Potential Enhancements**
- **Automated Grading System:** Enables automatic evaluation based on predefined test cases.
- **Plagiarism Detection Mechanism:** Ensures academic integrity by identifying similar code submissions.
- **Expanded Language Support:** Adds compatibility for additional programming languages.


## **Main Contributers**

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/hasanaliozkan-dev">
        <img src="https://github.com/hasanaliozkan-dev.png" width="100px;" alt="AliGithub"/>
        <br />
        <b>Hasan Ali Özkan</b>
        <br />
        Researcher Assistant
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/yarennoztekinn">
        <img src="https://github.com/yarennoztekinn.png" width="100px;" alt="AliGithub"/>
        <br />
        <b>Yaren Öztekin</b>
        <br />
        Full Stack Developer
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/mazlumemregirgin">
        <img src="https://github.com/mazlumemregirgin.png" width="100px;" alt="AliGithub"/>
        <br />
        <b>Mazlum Emre Girgin</b>
        <br />
        Full Stack Developer
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/meliskirik">
        <img src="https://github.com/meliskirik.png" width="100px;" alt="AliGithub"/>
        <br />
        <b>Melis Kırık</b>
        <br />
        Full Stack Developer
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/Serdar1048">
        <img src="https://github.com/Serdar1048.png" width="100px;" alt="MehmetGithub"/>
        <br />
        <b>Serdar Dedebaş</b>
        <br />
        Full Stack Developer
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/koraytacus">
        <img src="https://github.com/koraytacus.png" width="100px;" alt="AyseGithub"/>
        <br />
        <b>Koray Ürün</b>
        <br />
        Full Stack Developer
      </a>
    </td>
  </tr>
</table>






## **License**
GNU General Public License v3.0

For full terms and conditions, see the [LICENSE](LICENSE) file or visit the official license page:  
🔗 [[GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.html)

For further inquiries or contributions, please submit a pull request or reach out via the project's repository.
