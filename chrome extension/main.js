Addimage = function(info){
  var ImageURL = info.srcUrl;
  chrome.tabs.create({url: "http://localhost:9080/CreateFromExtension?term="+ImageURL});
};

chrome.contextMenus.create({
  title: "Add Image to Stream!",
  contexts:["image"],
  onclick: Addimage
});
