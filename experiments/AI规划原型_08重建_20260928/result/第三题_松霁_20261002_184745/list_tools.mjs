import {Client} from 'file:///Users/rinsing/Documents/文稿 - Rinsing的MacBook Air/project/StructureBinder/country_designer_mcp/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import {StdioClientTransport} from 'file:///Users/rinsing/Documents/文稿 - Rinsing的MacBook Air/project/StructureBinder/country_designer_mcp/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';
import {readFile,writeFile} from 'node:fs/promises';
const root='/Users/rinsing/Documents/文稿 - Rinsing的MacBook Air/project/StructureBinder';
const out=decodeURIComponent(new URL('.',import.meta.url).pathname).replace(/\/$/,'');
const client=new Client({name:'songji-question-three',version:'1.0'});
try {await client.connect(new StdioClientTransport({command:process.execPath,args:[root+'/country_designer_mcp/dist/index.js'],cwd:root,stderr:'pipe'}));
const result=await client.listTools();await writeFile(out+'/tool_schemas.json',JSON.stringify(result,null,2));
console.log(JSON.stringify(result.tools.filter(t=>/city_(query_structure|prepare_d4|compile_d4|plan_d4$|submit_d4)/.test(t.name)),null,2));
}finally{await client.close();}
