searchUrbanDict = function(word){
  var query = word.selectionText;
  chrome.tabs.create({url: "http://localhost:9080/CreateFromExtension"});
};

chrome.contextMenus.create({
  title: "Search in UrbanDictionary",
  contexts:["selection"],
  onclick: searchUrbanDict
});
