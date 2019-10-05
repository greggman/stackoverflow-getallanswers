const fs = require('fs');
const flow = require('xml-flow')

const userAnswersbyParentId = {};
const answersByParentId = {};
const questionsById = {};

var optionSpec = {
  options: [
   { option: 'in',  alias: 'i',  type: 'String',  required: true, description: 'xml file to read'},
   { option: 'out', alias: 'o',  type: 'String',  required: true, description: 'json file to write'},
   { option: 'userid',           type: 'String',  description: 'userid'},
   { option: 'username',         type: 'String',  description: 'username'},
   { option: 'help', alias: 'h', type: 'Boolean', description: 'displays help'},
   { option: 'debug',            type: 'Boolean', description: 'check more things'},
   { option: 'verbose',          type: 'Boolean', description: 'print more stuff'},
  ],
  helpStyle: {
    typeSeparator: '=',
    descriptionSeparator: ' : ',
    initialIndent: 4,
  },
};

const optionator = require('optionator')(optionSpec);
let args;

try {
  args = optionator.parse(process.argv);
} catch (e) {
  console.error(e);
  process.exit(1);  // eslint-disable-line
}

function printHelp() {
  console.log(optionator.generateHelp());
  process.exit(1);  // eslint-disable-line
};

if (args.help) {
  printHelp();
}

if (!args.userid && !args.username) {
  console.log('must specify at least one or the other, userid or username');
  printHelp();
}

function scan(filename, fn) {
  return new Promise((resolve, reject) => {
    const inFile = fs.createReadStream(filename);
    const xmlStream = flow(inFile);
    xmlStream.on('tag:row', fn);
    xmlStream.on('end', () => {
      inFile.close();
      resolve();
    });
  });
}

async function main() {
  console.log('scan1', args.in);
  await scan(args.in, (post) => {
    if (post.posttypeid === "2" &&
        ((args.userid && post.owneruserid === args.userid) ||
         (args.username && post.ownerusername === args.username))) {
      userAnswersbyParentId[post.parentid] = userAnswersbyParentId[post.parentid] || [];
      userAnswersbyParentId[post.parentid].push(post);
    }
  });

  console.log('scan2', args.in);
  await scan(args.in, (post) => {
    if (userAnswersbyParentId[post.id]) {
      questionsById[post.id] = post;
    } else if (userAnswersbyParentId[post.parentid]) {
      answersByParentId[post.parentid] = answersByParentId[post.parentid] || [];
      answersByParentId[post.parentid].push(post);
    }
  });

  const data = {
    questionsById,
    answersByParentId,
  };
  console.log('write', args.out);
  fs.writeFileSync(args.out, JSON.stringify(data, null, 2));
  console.log('done');
}

main();


