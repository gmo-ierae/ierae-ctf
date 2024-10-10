// $ deno run --allow-net --allow-read server.ts

import { serveFile } from 'https://deno.land/std@0.224.0/http/file_server.ts'

const notFounds = new Set<string>()

function finish() {
  const body = JSON.stringify([...notFounds.values()])
  notFounds.clear()
  return new Response(body, { headers: { 'content-type': 'application/json' } })
}

function add(query: string) {
  notFounds.add(query)
  return new Response("ok")
}

async function handler(request: Request): Promise<Response> {
  const url = new URL(request.url)
  console.log(url.toString())
  switch (url.pathname) {
    case '/finish':
      return finish()
    case '/add':
      {
        const q = url.searchParams.get('q') || ''
        return add(q)
      }
    default:
      return await serveFile(request, 'search.html')
  }
}

Deno.serve({ port: 3001, hostname: "0.0.0.0", handler })

