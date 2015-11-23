import logging
import trafaret as t

from flask import request
from flask.ext.api import FlaskAPI
from flask_swagger import swagger
from flask_debugtoolbar import DebugToolbarExtension
from flask.ext.api.decorators import set_parsers
from ql import schema

from factories import *
from models import *
from utils import *

app = FlaskAPI(__name__)
app.config.from_object('settings')

toolbar = DebugToolbarExtension(app)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


def user_query(email):
    return'''
    query Yo {
      user(email: \"%s\") {
            email,
            posts {
                title
                etags
                tags
                comments {
                    name
                    content
                }
            }
      }
    }
    ''' % email


@app.route('/ql', methods=['GET', 'POST'])
@set_parsers(GraphQLParser)
def index():
    """
    Example query

    # query Yo {
    #   user(email: "$email" ) {
    #         email,
    #         posts {
    #             title
    #             etags
    #             tags
    #             comments {
    #                 name
    #                 content
    #             }
    #         }
    #   }
    # }

    """
    query = request.data or user_query("idella00@hotmail.com")

    logger.debug('Query: %s', query)
    result = schema.execute(query)
    result_hash = format_result(result)
    return result_hash


@app.route('/ql/<user_id>/posts', methods=['POST'])
def create_post(user_id):

    post_schema = t.Dict({
        'title': t.String(min_length=2),
        'content': t.String(min_length=2),
        t.Key('tags', optional=True): t.List(t.String, min_length=2),
    })

    post_data = post_schema.check(request.data)
    user = User.objects.get_or_404(id=user_id)
    post = Post(autor=user, **post_data)
    post.save()
    logger.debug('New post id %d', post.id)
    return {}, 201


@app.errorhandler(t.DataError)
def handle_invalid_usage(error):
    logger.debug(vars(error))
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/health-check')
@app.route('/ping')
def health_check():
    """
    Health check
    """
    return {'reply': 'pong'}


@app.route("/spec")
def spec():
    swag = swagger(app)
    swag['info']['version'] = "1.0"
    swag['info']['title'] = "Demo of graphql API endpoint"
    return swag


if __name__ == '__main__':
    app.debug = app.config['DEBUG']
    app.run(host='0.0.0.0', port=5000)
