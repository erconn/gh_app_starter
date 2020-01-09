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

import codeowners
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
    installation_access_token = await utils.get_installation_access_token(
        gh,installation_id
    )
    maintainer = event.data["sender"]["login"]
    message = f"Thanks for installing me, @{maintainer}! (I'm a bot)."

    api_url = os.getenv("GH_API_URL")

    for repository in event.data["repositories"]:
        # The following only works on github.com, need to change the URL to work with Enterprise.
        #url = f"/repos/{repository['full_name']}/issues"
        issue_string = f"/repos/{repository['full_name']}/issues"
        url = api_url+issue_string
        response = await gh.post(
            url,
            data={"title": "erconn's bot was installed", "body": message},
            oauth_token=installation_access_token["token"],
        )
        issue_url = response["url"]

        await gh.patch(
            issue_url,
            data={"state": "closed"},
            oauth_token=installation_access_token["token"],
        )


# When a pull request is made, run a syntax check on the CODEOWNERS file
# https://help.github.com/en/github/creating-cloning-and-archiving-repositories/about-code-owners
# single file permissions WOULD make the most sense for this except for the fact that
# CODEOWNERS can exist in one of 3 locations.
@router.register("pull_request", action="opened")
async def pr_opened(event, gh, *args, **kwargs):
    installation_id = event.data["installation"]["id"]
    installation_access_token = await utils.get_installation_access_token(gh, installation_id)
    api_url = os.getenv("GH_API_URL")
    pr_url = event.data["pull_request"]["url"]
    pr_branch = event.data["pull_request"]["head"]["ref"]
    pr_repo = event.data["pull_request"]["head"]["repo"]["full_name"]
    repo_path = f"/repos/{pr_repo}/"
    #need to add branch

    # check for CODEOWNERS file in one of its 3 valid locations:
    # repo/CODEOWNERS, docs/CODEOWNERS, or .github/CODEOWNERS

    codeowners_encoded = None
    # repo root
    try:
        codeowners_url = api_url+repo_path
        response = await gh.getitem(codeowners_url)
        codeowners_encoded = response["content"]
    except:
        pass

    # docs directory
    try:
        docs_path = "docs/"
        codeowners_url = api_url+repo_path+docs_path
        response = await gh.getitem(codeowners_url)
        codeowners_encoded = response["content"]
    except:
        pass

    # .github directory
    try:
        gh_config_path = ".github/"
        codeowners_url = api_url+repo_path+gh_config_path
        response = await gh.getitem(codeowners_url)
        codeowners_encoded = response["content"]
    except:
        pass

    # if we didn't find the CODEOWNERS file in any of the above locations, codeowners_encoded should
    # still be None
    if codeowners_encoded == None:
        # block the pull request by setting mergeable_status
    else:
        # allow the pull request


if __name__ == "__main__":

    app = web.Application()

    app.router.add_routes(routes)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)
    web.run_app(app, port=port)
