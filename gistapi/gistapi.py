# coding=utf-8
"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""
import urllib3
import requests
from flask import Flask, jsonify, request


# *The* app object
app = Flask(__name__)


@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"


def gists_for_user(username):
    """Provides the list of gist metadata for a given user.

    This abstracts the /users/:username/gist endpoint from the Github API.
    See https://developer.github.com/v3/gists/#list-a-users-gists for
    more information.

    Args:
        username (string): the user to query gists for

    Returns:
        The dict parsed from the json response from the Github API.  See
        the above URL for details of the expected structure.
    """
    gists_url = 'https://api.github.com/users/{username}/gists'.format(
            username=username)
    response = requests.get(gists_url)
    # BONUS: What failures could happen?
    # using the try and expect statement check if if a bad request is made
    try:
        response.raise_for_status()
    # catch any HTTP errors, failures
    except requests.excpetions.HTTPError as e:
        print "Error: " + str(e)
    # BONUS: Paging? How does this work for users with tons of gists?
    try:
        response.json()
        return response.json()
    except Exception as e:
        print "Error: " + str(e)


@app.route("/api/v1/search", methods=['POST'])
def search():
    """Provides matches for a single pattern across a single users gists.

    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """
    post_data = request.get_json()
    # BONUS: Validate the arguments?
    # Loop through dictionary and check if key valuse username 
    # and pattern exists. If not return string "invalid arguments"
    if all (a in post_data for a in ("username","pattern")):
        username = post_data['username']
        pattern = post_data['pattern']

        result = {}
        successful_matches_list = []
        gists = gists_for_user(username)
        # BONUS: Handle invalid users?
        # check if there are gists else print "invalid users"
        if gists:
            for gist in gists:
                # REQUIRED: Fetch each gist and check for the pattern
                # on each loop the following happens:
                # search for specific gist by id with the requested pattern parameter
                # create url string, with the correct gist['id'] and pattern, using the positional formatting with the .format method
                # using the request module, make a get request from gistapi to github to recieve a response object
                # using the builtin JSON decoder from the response module to get the json dictionary 
                # if there is successful request producing an response then append that reponse dictionary
                # to the successful_matches_list type list. 
                gist_id = gist['id']
                r = 'https://api.github.com/gists/{gist_id}?q={pattern}'.format(gist_id=gist_id, pattern=pattern)
                # check for any issues in a try and except
                # checking for timeouts, many redirects, plain ole failures
                try:
                    response = requests.get(r)
                except requests.exceptions.TooManyRedirects:
                    # Tell the user their URL was bad and try a different one
                    print "There are too many redirects. You have used a bad URL, please try a different one."
                except requests.exceptions.RequestException as e:
                    # catastrophic error. bail.
                    print e
                if response.json():
                    response_json = response.json()
                    successful_matches_list.append(response_json)
                else:
                    print "No matches"
                # BONUS: What about huge gists?
                # BONUS: Can we cache results in a datastore/db?
                pass

            result['status'] = 'success'
            result['username'] = username
            result['pattern'] = pattern
            result['matches'] = successful_matches_list

            #print jsonify(result)
            return jsonify(result)
        else:
            return "invalid users from Github"
    else:
        return "invalid arguments"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
