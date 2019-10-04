# stackoverflow-getallanswers

some scripts to get all answers for a particular user

## How to Use

1. `npm install`

2. Download the stackoverflow data dump

   https://archive.org/details/stackexchange

   You probably only want stackoverflow.com-Posts.7z

3. Uncompress it

   ```sh
   7z x stackoverflow.com-Posts.7z
   ```

   This should result in a `Posts.xml` file.

   Note: ~70GIG!!!! for stackoverflow.com as of 2019-09
   Took nearly a hour to decompress

4. Run this script

   Go to a particular user's page on stackoverflow. For example, [Jon Skeet](https://stackoverflow.com/users/22656/jon-skeet).

   Notice the number in the url. `https://stackoverflow.com/users/22656/jon-skeet`. That's that user's userid

   ```sh
   node index.js --in=path/to/Posts.xml --out=path/to/output.json --userid=22656 --username="Jon Skeet"
   ```

   70gig gile, took several hours. Need to be read twice as not enough ram keep all in memory.
   First scan finds answers by specified user. Second scan finds questions for answers found in first scan.

Result is a .json file with an object of "questionsById" and object of "answersByParentId" so for each
question you can look up the answer to that question

```js
const db = JSON.parse(fs.readFileSync(filename, {encoding: 'utf8'));
for (const [questionId, question] of db.quesionsById) {
  const answer = db.answersByParentId[questionId];
  console.log('=================================');
  console.log(JSON.stringify(question, null, 2));
  console.log('---------------------------------');
  console.log(JSON.stringify(answer, null, 2));
}
```


