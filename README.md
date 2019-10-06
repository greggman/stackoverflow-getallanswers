# stackoverflow-getallanswers

some scripts to get all answers for a particular user

## How to Use

1. Download the stackoverflow data dump

   https://archive.org/details/stackexchange

   You probably only want `stackoverflow.com-Posts.7z` and `stackoverflow.com-Posthistory.7z`

3. Uncompress both of them

   ```sh
   7z x stackoverflow.com-Posts.7z
   7z x stackoverflow.com-Posthistory.7z
   ```

   This should result in a `Posts.xml` file and a `Posthistory.xml` file.

   Note: ~200GIG!!!! for stackoverflow.com as of 2019-09
   Took nearly 2 hours to decompress

3. Look up the user's id

   Go to a particular user's page on stackoverflow. For example, [Jon Skeet](https://stackoverflow.com/users/22656/jon-skeet).

   Notice the number in the url. `https://stackoverflow.com/users/22656/jon-skeet`. That's that user's userid. In this case `22656`

4. Run the script


   ```sh
   python getallanswers.py --posts=path/to/Posts.xml --posthistory=path/to/Posthistory.xml --out=path/to/output.json --userid=22656
   ```

   200gig file, took 8 hours. The Posts.xml file neeeds to be read twice as not enough ram keep all in memory.
   First scan finds answers by specified user. Second scan finds questions for answers found in first scan.
   Third scan reads Posthistory.xml to get the original markdown content as the user typed it, not the
   converted html which is all that's stored in Posts.xml

Result is a .json file with an object of "questionsById", an object of "answersByParentId", and
an object of "historyById" so for each question you can look up the answers and history for both

```js
const userId = '22656';
const db = JSON.parse(fs.readFileSync(filename, {encoding: 'utf8'));
for (const [questionId, question] of db.questionsById) {

  applyHistory(question, db.historyById[questionId])
  console.log('=================================');
  console.log(JSON.stringify(question, null, 2));

  const answers = db.answersByParentId[questionId](a => a.OwnerUserId === userId);
  for (const answer of answers) {
     applyHistory(answer, db.historyById[answer.Id]);
     console.log('---------------------------------');
     console.log(JSON.stringify(answer, null, 2));
  }
}

// puts the markdown for this post in post.Text
function applyHistory(post, history) {
  if (history.length) {
    history = history.sort((a, b) => a.CreationDate > b.CreationDate ? -1 : (a.CreationDate < b.CreationDate ? 1 : 0))
    post.Text = history[0].Text;
  }
}
```

## More info

https://meta.stackexchange.com/questions/2677/database-schema-documentation-for-the-public-data-dump-and-sede



