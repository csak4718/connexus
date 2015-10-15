Addimage = function(info){
  var ImageURL = info.srcUrl;
  chrome.tabs.create({url: "http://connexus-fall15.appspot.com/CreateFromExtension?term="+ImageURL});
};

chrome.contextMenus.create({
  title: "Add Image to Stream!",
  contexts:["image"],
  onclick: Addimage
});
