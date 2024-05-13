import os
import subprocess
from dotenv import load_dotenv
from argparse import ArgumentParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class CommandResponse(BaseModel):
    is_incorrect: bool = Field(default=False, description="Indicates if the command was incorrect")
    incorrect_command: str = Field(default='', description="The original incorrect command")
    incorrect_point: str = Field(default='', description="Highlighted incorrect part of the command")
    incorrect_reason: str = Field(default='', description="Explanation of why the command was incorrect")
    fixed_command: str = Field(default='', description="Corrected version of the command")

def get_shell():
    # 사용자의 기본 셸을 반환
    shell_path = os.getenv("SHELL", "/bin/bash")
    return os.path.basename(shell_path)

def get_recent_command():
    # 셸의 히스토리 파일에서 가장 최근의 명령어를 가져옴
    shell = get_shell()
    home = os.getenv("HOME", "/home/username")
    history_path = f"{home}/.{shell}_history"
    try:
        with open(history_path, "rb") as file:
            lines = file.readlines()
            return lines[-2].decode(errors="replace").strip().split(";")[-1]
    except FileNotFoundError:
        raise FileNotFoundError("History file not found.")

def fix_command(target_command):
    # GEMINI API를 사용하여 명령어를 수정
    load_dotenv()
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY environment variable is empty.")
    
    model = ChatGoogleGenerativeAI(model="gemini-pro", api_key=api_key, temperaterature=0)

    system_template = """
    [CONTEXT]
    Act a Linux expert.
    If an error occurs because [USER] executes an incorrect Linux command, it is your role to correct it with the correct command.
    To modify a command, follow the [STEP] below.

    [STEP]
    0.<evaluation command>
    Distinguishes whether this command is a correct command or an incorrect command. If the command is correct, {{is_incorrect}} is False, [STEP] 1. 2. 3. will not be performed. and
    {{incorrect_point}} says "none" and {{incorrect_reason}} says "This is a correct command." Enter the string called
    {{fixed_command}} The entered command is still inserted.
    If the command is incorrect, {{is_incorrect}} is True, perform [STEP] 1. 2. 3.
    1. {{incorrect_point}}
    Find the part where the command is incorrect and surround it with **. For example, the command "git commmit -m 'initial commit'" contains a mistake in the word 'commmit'. It should be highlighted to show the error, as in "git *commmit* -m 'initial commit'".
    2. {{incorrect_reason}}
    Take your time and explain why the command is incorrect.
    3. {{fixed_command}}
    Please correct the incorrect command and change it to the correct command.
    """

    user_template = """
    [INCORRECT_COMMAND]
    {target_command}

    [INSTRUCTION]
    Please change [INCORRECT_COMMAND] above to the correct command.

    The output format follows the json format below.
    {{
        "is_incorrect" : {{is_incorrect}},
        "incorrect_command" : {{incorrect_command}},
        "incorrect_point" : {{incorrect_point}},
        "incorrect_reason" : {{incorrect_reason}},
        "fixed_command" : {{fixed_command}}
    }}
    """

    prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(user_template),
            ]
        )
    
    chain = prompt | model | JsonOutputParser(pydentic_object=CommandResponse)
    completion = chain.invoke({"target_command" : target_command})

    return completion

def exec_fixed_command(fixed_command):
    # 수정된 명령어를 실행하고 결과를 반환
    result = subprocess.run(fixed_command, shell=True, capture_output=True, text=True)
    if result.stderr:
        return result.stderr
    return result.stdout

def main():
    # 주요 함수, 실행 인자에 따라 수정된 명령어를 실행할지 결정
    parser = ArgumentParser(description="Fix the last shell command.")
    parser.add_argument("-x", "--exec", action="store_true", help="Execute the fixed command.")
    args = parser.parse_args()

    try:
        target_command = get_recent_command()
        fix_command_response = fix_command(target_command)
        if not fix_command_response['is_incorrect']:
            print(f"Command: '{target_command}' is not incorrect.")
            return
        
        print(f"Command: {target_command}")
        print(f"Incorrect Point: {fix_command_response['incorrect_point']}")
        print(f"Incorrect Reason: {fix_command_response['incorrect_reason']}")
        print(f"Fixed Command: {fix_command_response['fixed_command']}")
        
        if args.exec:
            output = exec_fixed_command(fix_command_response['fixed_command'])
            print(f"Execution Output: {output}")
            
    except Exception as e:
        print(str(e))

if __name__ == "__main__":
    main()