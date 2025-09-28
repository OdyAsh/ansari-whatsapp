This file contains back-and-forth between Ansari members on various system design topics. It is intended to be a living document that evolves over time as new ideas and discussions arise.


# April 2025

## Waleed

@أشرف :] 🙌 Checking in to see how things are going -- how is the WhatsApp work going? Wanted to check in re the idea of a separate whatsapp microservice.

## Ashraf

 TL;DR: 
* infinite loop issue is still present 
* Carefully tracking the logs to see caused the loop is not easy (due to massive log of some messages) , so wrote code to dump some of these large logs to output files (json) to carefully examine message_history's progression
* Yielding entire result didn't fix the issue; it still yields part of the result (somehow), then anthropic is called again and again and again ...

---

https://stackoverflow.com/a/75047553/13626137

our old hypothesis was correct Amr; it is better to separate phone nums of testing and staging (even though that will cost us, so if we do this, then better create the new phone num for test app , as we WhatsApp webhook is called less in test than in staging i think?)

---

btw, here's a spoiler for what I think the issue was:

https://stackoverflow.com/questions/72894209/whatsapp-cloud-api-sending-old-message-inbound-notification-multiple-time-on-my/75815643#75815643

specifically:

the last comment:

https://stackoverflow.com/a/73161373/13626137

Therefore, longer claude messages exceed the default threshold (3000ms, i.e., 3 sec) so request gets sent, as can be in the definition of the callback_backoff_delay_ms here:

https://developers.facebook.com/docs/whatsapp/on-premises/reference/settings/app#parameters:~:text=Coreapp%20restart%20required.-,callback_backoff_delay_ms,-type%3A%20String

HOWEVER, the above page is for on-premise api, but I believe we're using cloud api:

https://developers.facebook.com/docs/whatsapp#:~:text=The%20platform%20consists%20of%20four%20primary%20APIs

Searched a lot, and apparently there's no way to set that parameter for cloud API

## Amr

Salam Ashraf, I had a look at the threads, this is my understanding:

1. Meta expects a 200 status response on webhooks calls, if we have a single phone number that is attached to multiple applications, all of them will have to return 200 response back to Meta, otherwise it will retry, so as you mentioned, make sure dev and staging and production are completely seperated from one another.
2. The actual processing of the user request shouldn't take place inside the webhook as it can take a while for the backend to prepare the respons (multiple tool calls, process response chunks, etc.).
3. There is a limit of 4,096 characters on whatsapp messages, and many of the responses will exceed this limit due to the inclusion of citations.
4. The webhook should receive the message, and immediately acknowledge by returning a 200 response.
5. Webhooks should be idempotent, meaning it should be possible for the API to be called multiple times with the same message without producing side effects.

These are my recommendations:
1. Create a seperate whatsapp repo that accesses the core Ansari package.
2. Whatsapp messages including message ID and timestampe should be logged in a database, when a new message is received, check if it hasn't been previously processed and if so log it, then queue the message for processing then return a 200 response (make sure the webhook is idempotent).
3. The actual processing of the message would be done seperetly, in the context of AWS, the webhook would create a queue message (SQS) than would be picked up by a Lambda function possibly created using Chalice, the function would then do the actual processing and return the message back to the user in chunks (to work around the 4k character limit).


## Ashraf

Already noticed what you said in point 2 (The actual processing of the user request shouldn't take place inside the webhook) and point 3 (There is a limit of 4,096 characters) and have implemented workarounds for them.

Regarding point 1 (Meta expects...), here's the thing:
* In meta, we have 1 business portfolio called "Ansari Project" , in it , we can connect multiple "whatsapp business accounts" . we currently have 2.   ... Ansari chat is connected to a phone number set up by Waleed , which gets billed upon interaction. On the contrary , "Test whatsapp business account" is connected to a test number provided by meta which doesn't get billed (as it's meta's way of helping developers debug their app without paying :))
* Now, apparently we can only create 1 test number
* however, we can create multiple billable phone numbers in "ansari chat" account
* So Waleed, there is an option to create a new phone number in "ansari chat" account, which will be billable (let's look for alternatives for now though to reduce costs).

---

Ok Amr  , reflecting again on (1.) . I see that there's no need to create a dedicated phone num. for staging (for now at least) . Here's why:

you're saying "when a num. sends a message, all instances (i.e., local/staging) have to send a 200 response". 

This is what I actually implemented in the upcoming PR; no matter what happens, we send a 200 response back to Meta, then continue running the task in the background; notice here the BackgroundTasks class? This is from fastapi. This allows us to make the webhook function directly return 200 , and in the background , any method inside background_tasks.add_task(...) will run.

E.g. , the send_whatsapp_message() which actually responds back to the user:

```python
background_tasks.add_task(presenter.send_whatsapp_message, from_whatsapp_number, " ... ")

# Actual code to process the incoming message using Ansari agent then reply to the sender
background_tasks.add_task(
presenter.handle_text_message,
from_whatsapp_number,
incoming_msg_text,

)

return Response(status_code=200)
``` 
So, no matter what happens in the background tasks, we always return 200 to Meta.

---

Done
https://github.com/ansari-project/ansari-backend/pull/171

---

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

Footnote [2]: I actually didn't do any env. var. changes nor have I read any docs/messages regarding our migration from PostgreSQL to Mongo , so if you know any docs. on how to setup the env. and/or new-db-schema and/or any tips to help me get things started, that would be great!


footnote [3]: I actually have no idea how to do step (5.) above, as Amr Masha'Allah has been doing phenomenal work in AWS/CI-CD/anything-environment-related , but it's hard for me to keep up , so if you can guide me to just a youtube playlist/tutorial or something, that will suffice 

(Note: I actually wish to learn how you did all of these prod. configurations, that's why I'm asking if you know any online guide to get me started)

## Waleed

Your plan seems largely aligned, but I think the way you should think about it is as a wrapper around the Ansari v2 api. My understanding is that you don’t really register accounts from whatsapp. So there are two options: (1) is to use the v1 style APIs which are much more stateless: conv history in, completion out. Then you store the results in your own database. I think this could simplify things a lot for you (2) register guest accounts. I don’t think we need an auth flow. As long as you keep the user id from the guest account, you can preserve the history of the conversation.


## Ashraf

How to connect to Mongo DB?

## Amr

There is no need to setup mongo locally, there is a dev DB you can connect to directly.

MONGO_URL="mongodb+srv://ansari-dev-user:<YOUR_PASSWORD>@ansarimongo.bmj1lq4.mongodb.net/?retryWrites=true&w=majority&appName=AnsariMongo"
MONGO_DB_NAME="ansari_dev_db"

Make sure to replace <YOUR_PASSWORD> with the password I shared with you privately.

## Ashraf

Okaaaay, so I just add that env. Variable when running locally , and that will connect it with mongo on staging?

What about the WhatsApp callback url tho;
I'm using zrok while testing locally , so i guess I don't need to do that , since your ngrok(?) callback url is already active in staging, correct?

## Amr

* There are 3 Mongo databases - dev, staging and production
* That connection string connects to the dev database which is seperate from the staging database
* Whatsapp staging is connected to the staging env in AWS
* zrok and ngrok are both dev reverse proxy tools, only used during development, they are not used in staging. Whatsapp staging and production connect directly to the respective AWS API (staging-api.ansari.chat and api.ansari.chat)
* The staging API is connected to the develop branch which currently has your latest updates (the ones that Waleed merged earlier).


## Ashraf

I believe if you try now , you'll get a typing indicator on whatsapp indicating that Ansari is typing a response

## Amr

Yes, I have just tried it, I got the typing indicator, but it didn't last until the background task was completed, I think WhatsApp has a typing indicator timeout of 25 seconds. (it does)

---

Generally speaking I would prefer to avoid resource sharing betwen envs (i.e. staging should use its own phone number).

## Ashraf

if we are ok with buying a new phone num on https://business.facebook.com/ , then sure I don't mind as well 🙌

## Amr

Does it have a monthly fee or is it PAYG?

## Ashraf

okaaay, so i read more on pricing policies, and from what I understand, we should now not pay anything!!

Details:


Starting November 1, 2024, service conversations are free for all businesses (free tier conversations are now unlimited instead of capped at 1,000). As a reminder, a customer service window must be open between you and a WhatsApp user before you can send the user a non-template message.
(source 1: https://developers.facebook.com/docs/whatsapp/pricing/updates-to-pricing#free-service-conversations)


Ok, so what's a "customer service window"?:
Whenever a WhatsApp user messages you, a 24-hour timer called a customer service window starts (or refreshes if one has already been started).
When a customer service window is open between you and a user, you can send any type of message to the user. If a window is not open between you and the user, you can only send template messages to the user
(source 2: https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages#customer-service-windows)

Moreover, what's a "service conversation"?: 
A service conversation is opened when any message other than a template message is delivered to your customer and no open conversation of any category exists between you and the customer.
(source: https://developers.facebook.com/docs/whatsapp/pricing#service-conversations)

Moreover, i'm looking at the entire pricing policy for whatsapp here:

https://developers.facebook.com/docs/whatsapp/pricing

And I don't see anything related to phone-num-registration costs :D
https://developers.facebook.com/docs/whatsapp/cloud-api/phone-numbers#registering-phone-numbers

So in that case, it's better to create a new phone number :) @Waleed

https://business.facebook.com/latest/whatsapp_manager/phone_numbers/?business_id=2677075122682873&tab=phone-numbers&nav_ref=whatsapp_manager&asset_id=456162294252988


---

I actually want to take your opinion on another matter before deploying to production @Amr @Waleed :

See this policy here?:

https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks#webhook-delivery-failure

"If we send a webhook request to your endpoint and your server responds with an HTTP status code other than 200, or if we are unable to deliver the webhook for another reason, we will keep trying with decreasing frequency until the request succeeds, for up to 7 days."

Therefore, if we enable prod. now , then the following will happen:
* for a user "bob" , the meta cloud API server will retry to send bob's ALL messages from 16/04 until today , and send them one by one to our ansari-backend production server
* Our server will reply to EACH ONE of these messages, thus bob's chat will be bombarded with responses of old messages that he sent throughout the week.

If we're ok with this (i.e., with the cost to be incurred, and to notify ansari-volunteers that this will happen), then you can enable whatsapp for production @Amr 👍

If not, give me some time, and I'll put a small snippet to check for the date of the incoming whatsapp message, and only accept messages sent today (and any other older message gets responded with 200, so that meta cloud API doesn't try to resend it)

## Amr

I think we should handle this scenario first, either check the timestamp and discard older messages, or better to store the message ID to make sure messages are only ever processed once.

## Ashraf

the latter solution that you mentioned won't solve this specific case i think. Let me explain with an example:

While ansari server is down, Let's say bob sent a message 3 days ago with ID: id1
Then sent another message 2 days ago with id: id2

Then , when we re-enable our ansari-server , and the messages are re-sent from meta api cloud to our server , then -> our server will  check the DB , and will still not find these id1/id2 , and so the server will process all requests and send them all to Bob

---

https://github.com/ansari-project/ansari-backend/pull/173

Done, should any of you accept this

Then I believe we'll be good to go with enabling prod. whatsapp ISA 🤝

## Waleed

Merged into staging. I think we should wait until @Amr is online to merge into prod ?

I think this is the last piece before we are ready to ship Ansari 3.0 ;-). Good work everyone. May Allah accept all the hard work we’ve put in to get to this point.

# May 2025

## Waleed

@Ashraf I just wanted to make sure this was on your radar: (attached screenshot of a sentry error)

I see a lot of these raw citation data errors.

## Ashraf

Done.

Kindly check this PR

https://github.com/ansari-project/ansari-backend/pull/180/

Since AnsariClaude is a central file, I made sure to activate my logic only if a runtime error occurs (to guarantee that it behaves the same way for web/mobile) , and runs the code-logic of except in the whatsapp case

## Waleed

Why not always use threads?

## Ashraf

tbh , i purely did that change on a basis of not modifying the original AnsariClaude logic 😅

but sure thing, i can modify it now to run only the threading code

## Waleed

I’m really surprised that switching from asyncio to threading makes a difference. Why do you think that is?

## Ashraf

I can answer that question. but how much granularity do you want in the answer?
(as it took me a culmination of 3 days worth of learning to understand asyncio vs threading flow XD)

Sobhan Allah, learned SO much about asynchronous programming since the "typing indicator infinite loop" issue 1.5 weeks back

VERY high level summary:

* in order for me to be able to send the "..." indicator while ansari is preparing the answer, I have to run things "in parallel"
* Asynchronous programming (i.e., asyncio) simulates that, but as a single thread, in a single process.
* Therefore, I run whatsapp-related logic asynchronously, but here's the catch: AnsariClaude is not asynchronous
* Therefore, I do this neat workaround in the attached code image INSTEAD OF response = [tok for tok in agent.replace_message_history(...)]
* This will allow the execution flow to go from handle_text_message to the function responsible for sending the "..." message each x amount of seconds ... and vice versa
* HOWEVER, this "jumping around" is done using asyncio's event loop.
* Now, the previous translation code used the asyncio.run method, which tries to create an event loop ..  but whatsapp_presenter.py already created one to do this hopping around
* This is why error happens specifically in whatsapp

soooo, don't worry , if you want, we may soon remove the threads logic when i migrate whatsapp to a dedicated repo 
(
even tho i think threads is a better option than asyncio.run anyways as this asyncio.run snippet will not allow ansari-backend repo to do any "hopping around" code logics by using async features. Details:

https://stackoverflow.com/a/70992886/13626137

However, we may never need to utilize that "hopping around" logic in the future, but I just thought I'd point it out :]


---

finished thread logic.

This was, more complicated, than I anticipated. Details in the commit message here: https://github.com/ansari-project/ansari-backend/pull/180/commits/00d43f4c352002850dc00a02b609c97754396c11

(Note: this commit message should have been written in the commit before the last one, i.e., refactor: citation translation using threads that was a misplacement from my end apologies)

---

Unfortunately, testing this use case is a bit tricky , as the following need to happen:

1. claude decides that answer needs citations (it doesn't do so sometimes even when I say provide citations , which is weird, but maybe bec. I've been testing rigorously lately)
2. then, the citations don't contain english version, BUT includes an Arabic version (this is a rare case to begin with, I tried with a lot of topics, and Masha Allah I always get multi language citation (which is cool))

Therefore, I temporarily hardcoded a bit to make sure these functions are reached and tested, and my - few - tests proved successful Alhamdullilah

(obviously, these hardcoded snippets are on my PC, nothing committed to github)

# August and September 2025

## Waleed

There’s a lot of stuff we need to do, I think. I think we’re ready for a new phase of Ansari development (towards Ansari v4): 

* ⁠We need to fix the issue with citations in WhatsApp.

## Ashraf

Can you remind me of the citations issue in Whatsapp? (Details)

## Waleed

We keep getting Sentry alerts that citations in WhatsApp are not working.

## Ashraf

Hello team!

Just added a PR to develop with a fix for the asyncio.run(...) issue for whatsapp webhooks.

I tested this with multiple calls locally, so this isn't a stress test (i.e., in case of prod, LOTS of users may access simultaneously, so we can monitor if the server will be slowed down or not in the case of whatsapp specifically).

All of the details are mentioned in the description of the PR:

https://github.com/ansari-project/ansari-backend/pull/189

please review and tell me your thoughts! 🙌


Worst case scenario: the server slows down while doing specific requests for whatsapp that require arabic-only citations to be translated to english. if this happens, we can revert by writing `pass` in the except block found in _translate_with_event_loop_safety() method.

this will return the exact behaviour that was present before i made this PR

again, all of these details are mentioned in the PR link above



