import {Client} from 'file:///Users/rinsing/Documents/文稿 - Rinsing的MacBook Air/project/StructureBinder/country_designer_mcp/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import {StdioClientTransport} from 'file:///Users/rinsing/Documents/文稿 - Rinsing的MacBook Air/project/StructureBinder/country_designer_mcp/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';
import {readFile,writeFile} from 'node:fs/promises';
const root='/Users/rinsing/Documents/文稿 - Rinsing的MacBook Air/project/StructureBinder';
const out=decodeURIComponent(new URL('.',import.meta.url).pathname).replace(/\/$/,'');
const client=new Client({name:'songji-question-three',version:'1.0'});
try {await client.connect(new StdioClientTransport({command:process.execPath,args:[root+'/country_designer_mcp/dist/index.js'],cwd:root,stderr:'pipe'}));
const call=JSON.parse(await readFile(process.argv[2],'utf8')); const start=new Date().toISOString();
let result;try{result=await client.callTool(call,undefined,{timeout:120000});}catch(e){result={error:String(e)}}
const record={start,end:new Date().toISOString(),...call,result};await writeFile(process.argv[2].replace('.request.json','.response.json'),JSON.stringify(record,null,2));console.log(JSON.stringify(result,null,2));
}finally{await client.close();}
