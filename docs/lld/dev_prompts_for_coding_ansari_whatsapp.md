These are the prompts that I wrote to the LLM (Claude Sonnet 3.7 or Gimini 2.5 Pro) (on [VSCode Agent Mode](https://www.youtube.com/watch?v=dutyOc_cAEU)) to generate most of the ansari-whatsapp repository. The prompts are in the order they were given to LLM (mostly). Also, I rarely paste the agent's response, so I only focus on my prompts. The agent's response is usually a code snippet or a file creation.

As a result, this file is mainly used as a reference for future developers to:
* Understand the thought process behind the implementation of the ansari-whatsapp repository.
* Understand the prompts that were given to LLM to generate the code.
* Quickly add/fix features in the repo by using prompts similar to the ones used in this file.
  * Disclaimer: The prompts may not be perfect, and the generated code may require some adjustments. However, they can serve as a good starting point.

---
---

***TOC:***

- [Chat 1 - Migration of WhatsApp Logic](#chat-1---migration-of-whatsapp-logic)
  - [Message 1](#message-1)
  - [Message 2](#message-2)
  - [Message 3](#message-3)
  - [Message 4](#message-4)
- [Chat 2 - Documentation System Setup](#chat-2---documentation-system-setup)
  - [Message 1](#message-1-1)
    - [DEV NOTE - VSCode's Custom Instructions](#dev-note---vscodes-custom-instructions)
- [Chat 2 - Env. Management Setup](#chat-2---env-management-setup)
  - [Message 1](#message-1-2)
- [Chat 3 - Logging to Loguru Migration](#chat-3---logging-to-loguru-migration)
  - [Message 1](#message-1-3)
- [Chat 4 - Migrate New Whatsapp Changes in ansari-backend to ansari-whatsapp](#chat-4---migrate-new-whatsapp-changes-in-ansari-backend-to-ansari-whatsapp)
  - [Message 1](#message-1-4)
  - [Message 2](#message-2-1)
    - [DEV NOTE - `#websearch`](#dev-note---websearch)
  - [Message 3](#message-3-1)
  - [Message 4](#message-4-1)
    - [DEV NOTE - `GitHub MCP`](#dev-note---github-mcp)
  - [Message 5](#message-5)
- [Chat 5 - Auto-Reloading Env Variables](#chat-5---auto-reloading-env-variables)
  - [Message 1](#message-1-5)
- [Chat 6 - Streaming Response Implementation](#chat-6---streaming-response-implementation)
  - [Message 1](#message-1-6)

---
---

Note: Each chat history (e.g., chat 1, etc.) is a separate conversation with LLM.

# Chat 1 - Migration of WhatsApp Logic

## Message 1

Here's the thing

see the whatsapp related logic in all of the #codebase  of ansari-backend repo? 

I want to migrate that into a dedicated repo (which i created a folder for in this workspace called ansari-whatsapp), such that ansari-whatsapp kind of acts like a frontend client , and calls the services found in ansari-backend. can you help me with this migration?
(again, the ansari-whatsapp folder where you can create files is found here: D:\CS\projects\ansari-whatsapp ) 

Tip: you may follow the chat below to have a visualization of what you can implement to get started (but you don't have to follow what's below word-by-word, just use the logic that you see fit, and then you be creative with what you think is best)

Here are the chat messages that may help you out:


```
junior:

regarding the separate whatsapp repo recommendation , I see that as well, since the whatsapp logic is becoming too big anyways

However, I want to have a mental model of what the main steps of this migration are. 

so for example:

1. main_whatsapp.py will obviously be migrated to the new repo, and the 2 fastapi endpoints in main_whatsapp.py will be like @app...() instead of @router...() 
2. all the env. vars. related to whatsapp will be moved to the WA repo
3. in whatsapp_presenter.py , I won't be able to write DB-related logic anymore since the DB is at ansari-backend repo , so I think I'll instead add endpoints like @app.post("/whatsapp/v2/threads/{wa_phone_num}") / ..."/whatsapp/v2/users/register" in ansari-backend's main_api.py and relocate the DB-related logic to it. (footnote [1,2] at the end)
4. I'll create a dedicated whatsapp_logger.py similar to ansari_logger.py
5. I'll mimic CI/CD of ansari-backend to whatsapp repo to make the 2 webhooks go live? (footnote [3] at the end)

Footnote [1]: I can't visualize the auth-flow here tho. So in the case of ansari.chat , we validate user with email/pass , but that will not be applicable here, so what do you suggest? ...
what I have in mind: if a new phone num. sends a message, we first return "will send SMS for verification, when you see it, kindly send us the code", and then the user sends the code, and then if it matches, the user is authenticated. However, we'll have to do this at the start of each "session" (currently set to 3 hours I guess) , so I think this is not very practical... any thoughts ?
```

```
senior:
Your plan seems largely aligned, but I think the way you should think about it is as a wrapper around the Ansari v2 api. My understanding is that you don't really register accounts from whatsapp. So there are two options: (1) is to use the v2 style APIs which are much more stateless: conv history in, completion out. Then you store the results in your own database. I think this could simplify things a lot for you (2) register guest accounts. I don't think we need an auth flow. As long as you keep the user id from the guest account, you can preserve the history of the conversation.
```

## Message 2

stop waiting for output from shell: start main api task; just continue your flow

## Message 3

great, few tweaks:

1. see the implementation of #sym:process_message ? it has a TO-DO , now replace the response_text placeholder currently implemented with the following: create an ansari agent at the top of the #file:whatsapp_router.py   file (similar to what's done in #file:main_api.py  ) , then use the agent logic found in #sym:handle_text_message   to complete TO-DO code. (however, i''m not sure if this is the optimal solution or not, so think for yourself as well)

2. try to make the implementation of #file:whatsapp_logger.py  similar to that of #file:ansari_logger.py (e..g., use rich library, etc)


## Message 4

great! quick question tho , i see that in vscode, when i ctrl+shift+v a .md file to set it to preview mode, the mermaid diagram still appears as text, not diagram , is there a vscode extension or something that we can install to fix this ? (search the net if you want #websearch ) 

if not, maybe replace that with references to a diagrams/ folder inside docs/ that has these mermaid code (i.e., .mermaid files)

# Chat 2 - Documentation System Setup

## Message 1

From now on, I want you to save any prompt that I write to you in #file:dev_prompts_for_coding_ansari_whatsapp.md  , taking into consideration these conditions/style-guides:

1. If my prompt is simple (e.g., fix this small issue, etc.) or it doesn't reflect a relatively big design choice for ansari-whatsapp/ansari-backend, then do NOT add it to the file.

2. Else, then when you add that prompt:

    2.1 If there are previous prompts before this one  in the current chat history of the IDE's GitHub Copilot Extension , then append it under a `## Message {NUMBER}` header

    2.2 Else, then create a new `# Chat {NUMBER} - {MAIN TOPIC THAT YOU INFER}` header, then under that , `## Message 1` , then, append the prompt under that.

### DEV NOTE - VSCode's Custom Instructions

Originally, I suffixed the above prompt with this:

> I'll see if you understand what I just said or not based on what you do right now after reading these instructions :]

As you can see:
* The agent understood the instructions and did what I asked for
  * I.e., the `# Chat ...`, `## Message ...` , `From now on ...` text were added by the agent to the file.
* ... But it removed the last part of the prompt 
  * (a lil' bit sentient for my taste, but I ain't complaining :p).

HOWEVER: 
* When you open a new chat in VSCode, it forgets about the above instructions.

Therefore, possible solutions: 

Method 1 (Currently used): Use VSCode's custom instructions feature:

1. Enable VSCode's [custom instructions](https://code.visualstudio.com/docs/copilot/copilot-customization#_define-codegeneration-custom-instructions) feature
2. Create a workspace which sees both repos (ansari-backend and ansari-whatsapp). 
   1. Specifically, copy the `ansari-whatsapp-backend.code-workspace` file to `ansari-whatsapp/.vscode/` folder (so that you can change other VSCode settings as you like).
   2. Then, open that `.code-workspace` file and understand/follow any `// comments` that you see there.
3. Paraphrase the above instructions to [suit VSCode's best practices](https://code.visualstudio.com/docs/copilot/copilot-customization#_tips-for-defining-custom-instructions) ([example](https://code.visualstudio.com/docs/copilot/copilot-customization#_use-settings)), then add it to `dev_instructions_to_ide.md` (I already did that, so this is just an FYI).


IMPORTANT CAVEAT: As of 2025-04-18, the custom instructions feature:
* Is in experimental mode, so it may not work as expected.
* Does not work in `Ask`/`edit` modes (based on my personal tests).
  * In other words, it only works in `Agent` mode.

Method 2: Use Claude Code, then you can execute commands that `CLAUDE.md` (its memory) regularly with instructions like the one above. 


# Chat 2 - Env. Management Setup

## Message 1

Ok so, ansari-backend repo uses uv library for env/package management (therefore, it has a #file:uv.lock and a #file:pyproject.toml ).

Therefore, I'd like you to make the necessary adjustments in ansari-whatsapp repo to be similar to that above setup.


# Chat 3 - Logging to Loguru Migration

## Message 1

I want you to do the following:

understand the loguru documentation using web search #websearch , specifically, the catch() wrapper here: #fetch : https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.catch

Then, update the #file:whatsapp_logger.py file so that it uses loguru instead of standard logging

accordingly, see all the #usages of #sym:get_logger across files in #folder:ansari_whatsapp folder , as well as the try ... except blocks that used to have the old logger , then instead of that try ... except, wrap the function with @logger.catch . NOTE though that this replacement should be done only if the try ... except block surrounds the entire code of the function not certain lines inside that function.

When doing step (3.) , you'll notice that some of the code inside except has extra logic, not just a log message, if that's the case, i'll think you'll need to utilize the reraise / onerror / default parameters of loguru's catch wrapper function.

Since this is a big task, apply steps (3.) and (4.) on the .py files that have whatsapp in their name , then confirm with me , if i say ok, continue with the rest of the files


# Chat 4 - Migrate New Whatsapp Changes in ansari-backend to ansari-whatsapp

## Message 1

add fastapi's backgroundtasks code to #file:main.py based on the logic found here:

#fetch : https://raw.githubusercontent.com/ansari-project/ansari-backend/85bb370992b7d9c64ed28fe1a8cc72278cebe3ba/src/ansari/app/main_whatsapp.py

## Message 2

I want the whatsapp repo to be similar to ansari-backend in some aspects , so kindly do these tasks:

I want similar ORIGINS logic, so see these resources in ansari-backend and mimic/adjust accordingly to ansari-whatsapp: #file:config.py , #file:.env.example , #sym:get_extended_origins (but obviously, this time, the origins accepted in production should be related to whatsapp services, so you can search the internet for their URLs #websearch )

I want the new typing indicator syntax found in whatsapp_presenter.py file here: #fetch : https://raw.githubusercontent.com/ansari-project/ansari-backend/85bb370992b7d9c64ed28fe1a8cc72278cebe3ba/src/ansari/presenters/whatsapp_presenter.py . Moreover, You'll see other logical changes between the file that i just linked and our current #file:whatsapp_presenter.py (for example, the updated file in the url now splits the message properly, instead of the hardcoded [:4000] message limit that we currently have), so your task is to update the entirety of our current presenter file with the updated file that I mentioned in the url.

### DEV NOTE - `#websearch`

NOTE: sometimes, the agent freezes (i.e., infitie loop) when you use the `#websearch` command.
* I think is a bug in the agent, and it may be fixed in the future.

## Message 3

changes are now actually found in #folder:ansari of ansari-backend repo , however, we want to now include them to ansari-whatsapp repo , so kindly , apply all the changes to #folder:ansari_whatsapp , and notify me if certain logics will cause the communication between ansari-whatsapp and ansari-backend to crash

## Message 4

ok, but double check that that's all the updates that you need to do , by running github MCP's get_pull_request_files command to get the changed files of PRs: #171 , #173

### DEV NOTE - `GitHub MCP`

If you don't understand what `get_pull_request_files` / MCP means, then check the following (in that order):
* Video: [The Future of AI in VS Code: MCP Servers Explained!](https://www.youtube.com/watch?v=Wp0p7iKH6ho)
* Video: [Visual Studio Code + Model Context Protocol (MCP) Servers Getting Started Guide | What, Why, How](https://www.youtube.com/watch?v=iS25RFups4A)
* [get_pull_request_files](https://github.com/github/github-mcp-server?tab=readme-ov-file#:~:text=get_pull_request_files)
* Optional:
  * To create a GitHub MCP server, you need a GitHub Personal Access token, which can be generated from here:
    * https://github.com/settings/personal-access-tokens
    * Give it these permissions: Read access to ***Copilot Chat*** and ***Copilot Editor Context*** , Read and Write access to ***gists*** 
  * To understand more about why MCP is useful: [How MCPs Make Agents Smarter (for non-techies)](https://www.youtube.com/watch?v=m0YrxLnFPzQ)

## Message 5

ok, it seems that there are some implementation aspects you're missing when migrating to ansari-whatsapp, so let me explain again:

I want you to understand the updated code of #file:main_whatsapp.py , and replicate that in #file:main.py

Then, do the same changes accordingly to the presenter files. I.e., check the updated content in #file:whatsapp_presenter.py , and make this logic in #file:whatsapp_presenter.py (while obviously considering that the ansari_whatsapp/presenters/whatsapp_presenter.py relies on #file:ansari_client.py and #file:api_presenter.py )

# Chat 5 - Auto-Reloading Env Variables

## Message 1

in here #file:config.py:1-130 , i notice that i need to restart vscode's terminal in order for new env. variables in .env file to take place; is there a way to modify #file:config.py:1-130  to mitigate this? (i.e., when i ctrl+s  , the server will reload and take in the new env. variables)

# Chat 6 - Streaming Response Implementation

## Message 1

See the implementation of #sym:AnsariClient  and this file? #file:whatsapp_router.py 

Here's the issue: 

The file in whatsapp_router takes a long time to respond to AnsariClient, so i need a way for whatsapp_router to say to AnsariClient "processing" so that no httpcore.ReadTimeout occurs. How to do that? (i.e., send any form of communication to show that connection is still alive) 

(Note: I know i can just increase the read timeout of AnsariClient like what's mentioned here: #fetch : https://www.python-httpx.org/advanced/timeouts/#:~:text=HTTPX%20is%20careful%20to%20enforce,5%20seconds%20of%20network%20inactivity. , but i don't want to do that)

Actually nevermind , i figured it out!:

Let's just change the implementation of #sym:process_message so that instead of this: `response = [tok for tok in agent_instance.replace_message_history(msg_history) if tok]` , we make it stream the response back to ansariClient. Obviously, this means we'll change the expected return value in both files from json-like string, to a just a streaming string of the response (so for example, if an error occurs, we don't stream "error" key, but we instead raise error)
