import { scrapeEmailsFromWebsite } from './prospector-mcp-email-finder/src/email-engine.js';
for (const u of process.argv.slice(2)) {
  try { const r = await scrapeEmailsFromWebsite(u); console.log(u, JSON.stringify(r)); }
  catch(e){ console.log(u, 'ERR', String(e)); }
}
