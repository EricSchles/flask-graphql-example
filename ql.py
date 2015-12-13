import logging
from functools import lru_cache

import graphene
import trafaret as t

from models import Post, User


logger = logging.getLogger(__package__)


@lru_cache()
def get_comments_by_id(post_id):
    return Post.objects.get(id=post_id).comments


def construct(object_type, mongo_obj):
    field_names = [f.attname for f in object_type._meta.fields]
    if 'id' in field_names:
        field_names.append('_id')
    kwargs = {attr: val for attr, val in mongo_obj.to_mongo().items()
              if attr in field_names}
    if '_id' in kwargs:
        kwargs['id'] = kwargs.pop('_id')
    return object_type(**kwargs)


class CommentField(graphene.ObjectType):
    content = graphene.String()
    name = graphene.String()


class PostField(graphene.ObjectType):
    id = graphene.Int()
    title = graphene.String()
    tags = graphene.List(graphene.String)
    etags = graphene.String()
    comments = graphene.List(CommentField)
    comments_count = graphene.Int()

    def resolve_etags(self, *a, **_):
        return "( {} )".format(self.tags)

    def resolve_comments(self, *a, **_):
        return [construct(CommentField, c) for c in get_comments_by_id(self.id)]


class UserField(graphene.ObjectType):
    id = graphene.String()
    email = graphene.String()
    last_name = graphene.String()
    posts = graphene.List(PostField)

    @graphene.resolve_only_args
    def resolve_posts(self):
        posts = Post.objects.filter(author=self.id)
        return [construct(PostField, p) for p in posts]


class UserMutation(graphene.Mutation):

    class Input(object):
        """Params for User class"""
        first_name = graphene.String()
        last_name = graphene.String()
        email = graphene.String()

    user = graphene.Field(UserField)

    @classmethod
    def mutate(cls, _, info, __):
        logger.debug("agrs %s", info)
        user_schema = t.Dict({
            'email': t.String(min_length=2),
            'first_name': t.String(min_length=2),
            'last_name': t.String(min_length=2),
        })

        user_data = user_schema.check(info)
        user = User.objects.create(**user_data)
        user.save()
        return cls(user=construct(UserField, user))


class UserQuery(graphene.ObjectType):
    user = graphene.Field(UserField, email=graphene.Argument(graphene.String))
    ping = graphene.String(description='Ping someone',
                           to=graphene.Argument(graphene.String))

    def resolve_user(self, args, info):
        u = User.objects.get(email=args.get('email'))
        return construct(UserField, u)

    def resolve_ping(self, args, info):
        return 'Pinging {}'.format(args.get('to'))


class UserMutationQuery(graphene.ObjectType):
    create_user = graphene.Field(UserMutation)

schema = graphene.Schema(query=UserQuery, mutation=UserMutationQuery)
