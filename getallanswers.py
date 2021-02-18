#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import json
import os
import pickle
import sys
import time
import xml.sax
from optparse import OptionParser

def dictFromAttrs(attrs):
    d = {}
    for k, v in attrs.items():
        d[k] = v
    return d

class UserAnswersStreamHandler(xml.sax.handler.ContentHandler):

    def __init__(self, userId, userAnswers):
        self.userId = userId
        self.userAnswersByParentId = userAnswers

    def startElement(self, name, attrs):
        if name == 'row':
            if 'PostTypeId' in attrs and attrs['PostTypeId'] == '2' and 'OwnerUserId' in attrs and attrs['OwnerUserId'] == self.userId:
                parentId = attrs['ParentId']
                if not parentId in self.userAnswersByParentId:
                    self.userAnswersByParentId[parentId] = []
                self.userAnswersByParentId[parentId].append(dictFromAttrs(attrs))

class QuestionStreamHandler(xml.sax.handler.ContentHandler):

    def __init__(self, userAnswers, _answersByParentId, _questionsById):
        self.userAnswersByParentId = userAnswers
        self.answersByParentId = _answersByParentId
        self.questionsById = _questionsById

    def startElement(self, name, attrs):
        if name == 'row':
            id = attrs['Id']
            if id in self.userAnswersByParentId:
                self.questionsById[id] = dictFromAttrs(attrs)
            elif 'ParentId' in attrs:
                parentId = attrs['ParentId']
                if parentId in self.userAnswersByParentId:
                    if not parentId in self.answersByParentId:
                        self.answersByParentId[parentId] = []
                    self.answersByParentId[parentId].append(dictFromAttrs(attrs))

#
class HistoryStreamHandler(xml.sax.handler.ContentHandler):

    def __init__(self, _ids, _postsById):
        self.ids = _ids
        self.postsById = _postsById

    def startElement(self, name, attrs):
        if name == 'row':
            if 'PostHistoryTypeId' in attrs and (attrs['PostHistoryTypeId'] == '2' or attrs['PostHistoryTypeId'] == '5'):
                id = attrs['PostId']
                if id in self.ids:
                    if not id in self.postsById:
                        self.postsById[id] = []
                    self.postsById[id].append(dictFromAttrs(attrs))

#
class UsersStreamHandler(xml.sax.handler.ContentHandler):

    def __init__(self, _ids, _usersById):
        self.ids = _ids
        self.usersById = _usersById

    def startElement(self, name, attrs):
        if name == 'row':
            if 'Id' in attrs:
              id = attrs['Id']
              if id in self.ids:
                self.usersById[id] = dictFromAttrs(attrs)

def save(filename, obj):
  f = open(filename, 'wb')
  pickle.dump(obj, f)
  f.close()

def load(filename):
  f = open(filename, 'rb')
  obj = pickle.load(f)
  f.close()
  return obj

if __name__ == '__main__':
    # use default ``xml.sax.expatreader``
    parser = OptionParser()
    parser.add_option("--posts",       dest="posts",       help="posts.xml file", )
    parser.add_option("--posthistory", dest="posthistory", help="posthistory.xml file", )
    parser.add_option("--users",       dest="users",       help="users.xml file (optional)", )
    parser.add_option("--userid",      dest="userid",      help="userid", )
    parser.add_option("--out",         dest="out",         help="json to write", )
    parser.add_option("--temp",        dest="temp",        help="save/load temp files", action="store_true", default=False)

    (options, args) = parser.parse_args()
    if options.posts == None:
        print "--posts file not specified"
        sys.exit(1)
    if options.posthistory == None:
        print "--posthistory file not specfied"
        sys.exit(1)
    if options.userid == None:
        print "--userid not specified"
        sys.exit(1)
    if options.out == None:
        print "--out json file not specified"
        sys.exit(1)

    print "searching for", options.userid

    parser = xml.sax.make_parser()
    userAnswersByParentIdFilename = 'userAnswersByParentId.pickle'
    answersByParentIdFilename = 'answersByParentId.pickle'
    questionsByIdFilename = 'questionsById.pickle'
    historyByIdFilename = 'historyById.pickle'
    userAnswersByParentId = {}
    answersByParentId = {}
    questionsById = {}
    historyById = {}
    usersById = {}

    print "scan 1: find answers by userid", options.userid, "in", options.posts
    if options.temp:
      if os.path.exists(userAnswersByParentIdFilename):
        userAnswersByParentId = load(userAnswersByParentIdFilename)

    if len(userAnswersByParentId) == 0:
      ush = UserAnswersStreamHandler(options.userid, userAnswersByParentId)
      parser.setContentHandler(ush)
      with open(options.posts) as f:
          parser.parse(f)

      if options.temp:
        save(userAnswersByParentIdFilename, userAnswersByParentId)

    print "found", len(userAnswersByParentId), "answers by userid", options.userid

    if len(userAnswersByParentId) > 0:

        print "scan 2: get questions for answers in", options.posts
        if options.temp:
          if os.path.exists(answersByParentIdFilename) and os.path.exists(questionsByIdFilename):
            answersByParentId = load(answersByParentIdFilename)
            questionsById = load(questionsByIdFilename)

        if len(answersByParentId) == 0:
          qsh = QuestionStreamHandler(userAnswersByParentId, answersByParentId, questionsById)
          parser.setContentHandler(qsh)
          with open(options.posts) as f:
              parser.parse(f)

          if options.temp:
            save(answersByParentIdFilename, answersByParentId)
            save(questionsByIdFilename, questionsById)

        ids = {}
        for k in questionsById.keys():
            ids[k] = True
        for k,answers in answersByParentId.items():
            for answer in answers:
                ids[answer['Id']] = True

        print "scan 3: get markdown for Qs&As in", options.posthistory
        if options.temp:
          if os.path.exists(historyByIdFilename):
            historyById = load(historyByIdFilename)

        if len(historyById) == 0:
          hsh = HistoryStreamHandler(ids, historyById)
          parser.setContentHandler(hsh)
          with open(options.posthistory) as f:
              parser.parse(f)

          if options.temp:
            save(historyByIdFilename, historyById)

        if options.users != None:
          print "scan 4: get user info for Qs&As in", options.users

          # NOTE: If a user has deleted their account, stack overflow
          # no longer connects their questions or answers to their
          # account id.

          userIds = {}
          for item in questionsById.values():
            if 'OwnerUserId' in item:
              userIds[item['OwnerUserId']] = True
 
          for answers in answersByParentId.values():
            for answer in answers:
              if 'OwnerUserId' in answer:
                userIds[answer['OwnerUserId']] = True
 
          ush = UsersStreamHandler(userIds, usersById)
          parser.setContentHandler(ush)
          with open(options.users) as f:
            parser.parse(f)

    print "write json:", options.out
    with open(options.out, "w") as file:
        file.write(json.dumps({
            'questionsById': questionsById,
            'answersByParentId': answersByParentId,
            'historyById': historyById,
            'usersById': usersById,
        }, indent = 2))



