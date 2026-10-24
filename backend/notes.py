"""my personal note to myself about this project

get memwal memory and supabase key, including the memwal memory 
api key


memory parameters - what will the ai add to the memory function call

use fashion as a guide for the ai's behavior and test it


Campaign in progress
Last updated 12 min ago
Good marketing starts with a better read.
Turn cultural signals

kloppy should also give the business a channel to reach the audience
you can teams to a campaign and they can work together and also you can 
add teammates to a business, because we treat each account as a business, maybe add add 
multiple businesses

add popup question like in claude co work for agent specific questions and also request popup question and permission request if there are any

mode will have different prompts
ability to create documents and there will be an artifact

Stack decisions:
- Supabase Postgres/Auth/Storage with tenant-scoped RLS.
- Strands Agents SDK orchestrates the agent and MCP connector tools.
- Memwal stores explicit, tenant-scoped long-term memory.
- WebSocket is the primary chat transport; HTTP remains a reconnect fallback.
- Kloppy uses one intent-driven agent that chooses appropriate research,
  planning, drafting, and authorized actions from the user's request.
- The composer exposes permission policy, file attachments, knowledge context,
  and campaign skills. OpenRouter uses its free model router by default.


skills in knowledge page and can be invoked into the chat


set up amd memwal for this project and then openrouter free endpoint or anybetter one


remembwe we are using qloo


Kloppy is one agent; infer the user's intent and use the workflow steps needed.

klayeer
klood or clood

use security first approach
add don't rely on your training data always do proper research and be grounded


connect canva to the mcp and add proper comments, when coding from now henceforth andin the error 
logging add proper english meaning, so a human can know what exactly is wrong and where it went wrong
"""

