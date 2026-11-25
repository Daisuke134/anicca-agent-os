tell application "Google Chrome"
  set URL of active tab of front window to "https://studio.youtube.com/channel/UCFGkrtiSTni-AZ9DUY6Q5EA/videos"
end tell
delay 12
tell application "Google Chrome"
  execute front window's active tab javascript "document.title + '|' + location.href + '|' + document.readyState + '|' + (document.body ? document.body.innerText.slice(0, 200) : 'NOBODY')"
end tell
