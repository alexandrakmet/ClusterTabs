var tags = [];

function getInnerTextFromSelectorAll(selector) {
    return [...document.querySelectorAll(selector)].map((el) => el.innerText)
}

chrome.runtime.onMessage.addListener(
    function (request, sender, sendResponse) {
        if (request.type === "tags") {
            if (tags.length > 0) {
                sendResponse({
                    type: "tags",
                    tags: tags,
                });
            } else {
                sendResponse({
                    type: "pageData",
                    title: document.title,
                    texts: document.body.innerText,
                    headers: getInnerTextFromSelectorAll("h1, h2, h3, h4, h5, h6"),
                    styledTexts: getInnerTextFromSelectorAll("em, mark, cite, dfn, i, strong, b, u")
                });
            }
        } else if (request.type == "set_tags") {
            tags = request.tags;
        } else if (request.type == "content") {
            sendResponse({
                type: "content",
                content: document.body.innerText
            })
        }
    }
);