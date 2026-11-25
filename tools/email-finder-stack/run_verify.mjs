import { verifyEmail, verifyMX, scrapeEmailsFromWebsite } from './prospector-mcp-email-finder/src/email-engine.js';
const emails = process.argv.slice(2);
for (const e of emails) {
  try { const r = await verifyEmail(e); console.log(JSON.stringify(r)); }
  catch(err){ console.log(JSON.stringify({email:e, error:String(err)})); }
}
