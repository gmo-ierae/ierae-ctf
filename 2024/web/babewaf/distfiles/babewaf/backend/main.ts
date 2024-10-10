import { Hono } from 'hono'
import { serveStatic } from 'hono/deno'

const app = new Hono()
const FLAG = Deno.env.get("FLAG");

app.get('/', serveStatic({ path: './index.html' }))

app.get('/givemeflag', (c) => {
  return c.text(FLAG)
})

export default app
