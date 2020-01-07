import asyncio
import os
import sys
import traceback


import aiohttp
from aiohttp import web
import cachetools
from gidgethub import aiohttp as gh_aiohttp
from gidgethub import routing
from gidgethub import sansio


from webservice import utils

router = routing.Router()
cache = cachetools.LRUCache(maxsize=500)

routes = web.RouteTableDef()


@routes.get("/", name="home")
async def handle_get(request):
    return web.Response(text="Hello world")


@routes.post("/webhook")
async def webhook(request):
    try:
        body = await request.read()
        secret = os.environ.get("GH_SECRET")
        event = sansio.Event.from_http(request.headers, body, secret=secret)
        if event.event == "ping":
            return web.Response(status=200)
        async with aiohttp.ClientSession() as session:
            gh = gh_aiohttp.GitHubAPI(session, "demo", cache=cache)

            await asyncio.sleep(1)
            await router.dispatch(event, gh)
        try:
            print("GH requests remaining:", gh.rate_limit.remaining)
        except AttributeError:
            pass
        return web.Response(status=200)
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        return web.Response(status=500)

# Create and close an issue thanking the maintainer whenever the bot is installed on a repository
@router.register("installation", action="created")
async def repo_installation_added(event, gh, *args, **kwargs):
    installation_id = event.data["installation"]["id"]
    access_token_url = event.data["installation"]["access_tokens_url"]
    installation_access_token = await utils.get_installation_access_token(
        gh,installation_id,access_token_url
    )
    maintainer = event.data["sender"]["login"]
    message = f"Thanks for installing me, @{maintainer}! (I'm a bot)."

    #REALLY hackish way of getting the base URL. There's got to be something better.
    #basically just subtracting "/installation/repositories" from the end of the repositories_url in the event payload
    # which usually looks something like: "https://rtp-scm-github3.cisco.com/api/v3/installation/repositories"
    repositories_url = event.data["installation"]["repositories_url"]
    base_url = repositories_url[:-26]

    #key name has changed to "repositories", not "repositories_added".
    for repository in event.data["repositories"]:
        #url = f"/repos/{repository['full_name']}/issues/" # This needs to be changed to whatever URL is in the response
                                                           # as this format only works on github.com
        issue_string = f"/repos/{repository['full_name']}/issues/"
        url = base_url+issue_string
        print(f"Creating installation issue in repository {repository['full_name']}")
        response = await gh.post(
            url,
            data={"title": "erconn's bot was installed", "body": message},
            oauth_token=installation_access_token["token"],
        )
        issue_url = response["url"]
        print(f"Closing issue {response['number']}")
        await gh.patch(issue_url, data={"state": "closed"}, oauth_token=installation_access_token["token"])
    #pass


if __name__ == "__main__":  # pragma: no cover
    app = web.Application()

    app.router.add_routes(routes)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)
    web.run_app(app, port=port)
