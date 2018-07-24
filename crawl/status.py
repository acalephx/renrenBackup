# coding: utf8

from datetime import datetime
import json

from config import crawl_config as config
from models import Status

from .crawler import crawler
from .utils import get_comments, get_likes


def load_status_page(page):
    resp = crawler.get_url(config.STATUS_URL, {'uid': config.COOKIES['id'], 'curpage': page})
    r = json.loads(resp.text)

    likes = r['likeInfoMap']
    for s in r['doingArray']:
        id = int(s['id'])
        status = {
            'id': id,
            't': datetime.fromtimestamp(int(s['createTime'])/1000),
            'content': s['content'],                            # 内容
            'like': likes.get(f'status_{id}', 0),               # 点赞
            'repeat': s['repeatCountTotal'],                    # 转发
            'comment': s['comment_count'],                      # 评论
            'rootContent': s.get('rootContent', ''),            # 如果是转发，转发的原文
            'rootUid': s.get('rootDoingUserId', 0),             # 转发原 uid
            'rootUname': s.get('rootDoingUserName', ''),        # 转发原 username
        }
        Status.insert(**status).on_conflict('replace').execute()

        if status['comment'] > 0:
            get_comments(id, 'status')
        if status['like'] > 0:
            get_likes(id, 'status')

    parsed = len(r['doingArray'])
    print(f'  on page {page}, {parsed} parsed')

    return r['count']


def get_status():
    cur_page = 0
    total = config.STATUS_PER_PAGE
    while cur_page*config.STATUS_PER_PAGE < total:
        print(f'start crawl status page {cur_page}')
        total = load_status_page(cur_page)
        cur_page += 1

    return total