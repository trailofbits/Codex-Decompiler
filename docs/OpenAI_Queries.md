# OpenAI Queries Used in this Plugin
For example purposes, the source file that was imported into Ghidra is shown below. All of the queries were generated based on this source file.
```c
#include <stdio.h>
#include <string.h>

int main() {
	printf("Enter the password: ");
	char password[20];
	gets(password);
	if (strcmp(password, "password123") == 0) {
		printf("Correct password!\n");
		return 1;
	}
	else {
		printf("Incorrect password!\n");
		return 0;
	}
}
```
## Decompiler Query
This query is used to take the disassembly from Ghidra and convert into decompiled code. The query is passed to the code-davinci-002 model from OpenAI in completion mode. 
```asm
x86 64-bit Assembly:

__stdcall main():
PUSH RBP
MOV RBP,RSP
SUB RSP,0x20
MOV dword ptr [RBP + -0x4],0x0
LEA RAX,[0x102008]
...
CALL puts
LAB_001011de:
MOV EAX,0x0
LEAVE
RET
//end of function main

Generate the C code that produced the above x86 64-bit assembly. The C code is idiomatic and uses functions, types, and structures from standard libraries.
```
### Output
```c
#include <stdio.h>
#include <string.h>

int main() {
	printf("Enter the password: ");
	char password[20];
	gets(password);
	if (strcmp(password, "password123") == 0) {
		printf("Correct password!\n");
		return 1;
	}
	else {
		printf("Incorrect password!\n");
		return 0;
	}
}
```
### Notes/Limitations
This is the main functionality of the plugin and as shown above, feeding the disassembly to the codex model often leads to great results. Compared to the original pseudocode provided by Ghidra, this code is much more verbose and easier to understand. From all my testing with different languages and different types of code, I can see that OpenAI's codex model is able to decompile code pretty well from Ghidra. One shortcoming of the model is that it requires that there are some symbols included in the binary. With symbols, the model is able to generate a more accurate decompilation. From my testing, the model still works without symbols but the results are less reliable. Finally, when calling the API for this model, I have passed a couple of parameters to improve the output. Specifically, the temperature parameter is set to zero to make the output more "deterministic", and the max_tokens parameter is set to a default value of 512.
## Generate Context Query
This query is used to generate a description for the decompiled code. The query is passed to the code-davinci-002 model from OpenAI in completion mode. 
```c
Understand the following code and generate a description for it as a comment.

Code:
#include <stdio.h>
#include <string.h>

int main() {
	printf("Enter the password: ");
	char password[20];
	gets(password);
	if (strcmp(password, "password123") == 0) {
		printf("Correct password!\n");
		return 1;
	}
	else {
		printf("Incorrect password!\n");
		return 0;
	}
}
```
### Output
```c
/*
This program asks the user to enter a password. If the password is correct, the program will print "Correct password!" and return 1. If the password is incorrect, the program will print "Incorrect password!" and return 0.

*/
#include <stdio.h>
#include <string.h>

int main() {
	printf("Enter the password: ");
	char password[20];
	gets(password);
	if (strcmp(password, "password123") == 0) {
		printf("Correct password!\n");
		return 1;
	}
	else {
		printf("Incorrect password!\n");
		return 0;
	}
}
```
### Notes/Limitations
This feature is able to generate a text description of the decompiled code with high accuracy. The accuracy of the description directly relates with the complexity of the code. With many complex functions, I've noticed that the description is not accurate or does not make sense. At the same time, I've also tried this query with some closed source windows libraries and it worked well in those scenarios. Thus, it seems that the stability of this feature is highly dependent on the executable.
## Re-generate Pseudocode Query
This query takes the exact same form and same model as the Decompiler Query. The main difference is that the temperature parameter of the model is set to 0.25 to decrease the deterministic nature of the decompiler query and generate another different result. The output of this query is always some decompiled code that is different to the output from the decompiler query. The purpose of the query is to keep generating different decompilations using the model until one works.
## Find Vulns Query
This query is used to find possible vulnerabilities in the decompiled code. The query is fed to the text-davinci-003 model from OpenAI in completion mode.
```c
Find any possible vulnerabilities in the following code. Describe the cause of the bug and possible ways to trigger it in a code comment.
Code:

#include <stdio.h>
#include <string.h>

int main() {
	printf("Enter the password: ");
	char password[20];
	gets(password);
	if (strcmp(password, "password123") == 0) {
		printf("Correct password!\n");
		return 1;
	}
	else {
		printf("Incorrect password!\n");
		return 0;
	}
}
```
### Output
```c
/* Possible vulnerability: The program is vulnerable to a buffer overflow attack because it uses the gets() function to read user input. This function does not check the size of the input, so if the user enters a string longer than the size of the buffer (20 characters in this case), it will overwrite other parts of the program's memory. This can be triggered by entering a string longer than 20 characters.*/

#include <stdio.h>
#include <string.h>

int main() {
	printf("Enter the password: ");
	char password[20];
	gets(password);
	if (strcmp(password, "password123") == 0) {
		printf("Correct password!\n");
		return 1;
	}
	else {
		printf("Incorrect password!\n");
		return 0;
	}
}
```
### Notes/Limitations
The text model is able to understand the decompiled code and then describe possible vulnerabilities. From my testing, it is able to find use after frees, double frees, buffer overflows, and other types of vulnerabilities. Like the description query, this query is directly correlated with the complexity of the code. If the decompiled code is inaccurate or too complex, the language model is unable to detect certain vulnerabilities. This query is also sent to the text model instead of the codex model because my testing has shown that the text model is more robust at understanding code.

## Ghidra Pseudocode Decompiler Query
This query takes the pseudocode that Ghidra generates and feeds that to the OpenAI api to further decompile the code. The query is sent to the code-davinci-002 model from OpenAI in completion mode.

### Query 
```c
Understand this code and rewrite it in a better manner with more descriptive function/variable names, better logic, and more.
Code:

undefined8 main(void)

{
  int iVar1;
  char local_1b [15];
  int local_c;
  
  local_c = 0;
  puts("\n Enter the password : ");
  gets(local_1b);
  iVar1 = strcmp(local_1b,"password123");
  if (iVar1 == 0) {
    puts("\n Correct Password ");
    local_c = 1;
  }
  else {
    puts("\n Wrong Password ");
  }
  if (local_c != 0) {
    puts("\n Root privileges given to the user ");
  }
  return 0;
}

New Code:
```
### Output
```html
<code>#include &lt;stdio.h&gt;
#include &lt;string.h&gt;

int main(void)
{
    char password[15];
    int isCorrect = 0;

    printf("\n Enter the password : ");
    scanf("%s", password);

    if (strcmp(password, "password123") == 0)
    {
        printf("\n Correct Password ");
        isCorrect = 1;
    }
    else
    {
        printf("\n Wrong Password ");
    }

    if (isCorrect)
    {
        printf("\n Root privileges given to the user ");
    }

    return 0;
}
</code>
```
### Notes/Limitations
Similar to the decompiler query, this query is able to decompile code from the Ghidra pseudocode and creates output that is much more readable and concise than the built-in decompiler. The main problem with this query is that sometimes when you call the api, the output is put in html code brackets and is html encoded as shown above. I have tried to change the query to solve this, but so far I have not been able to fix this.
