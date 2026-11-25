tell application "Google Chrome"
  execute front window's active tab javascript "location.href='https://studio.youtube.com/channel/UCFGkrtiSTni-AZ9DUY6Q5EA/videos'"
end tell
delay 15
tell application "Google Chrome"
  execute front window's active tab javascript "document.title + '|' + location.href + '|' + document.readyState + '|' + (document.body ? document.body.innerText.slice(0, 300) : 'NOBODY')"
end tell
