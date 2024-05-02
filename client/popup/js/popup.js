const serverUrl = "http://192.168.1.11:5000"
const tabGroupColor = {
    "grey": [95, 99, 104, 255],
    "blue": [26, 115, 232, 255],
    "red": [217, 48, 37, 255],
    "yellow": [249, 171, 0, 255],
    "green": [24, 128, 56, 255],
    "pink": [208, 24, 132, 255],
    "purple": [161, 66, 244, 255],
    "cyan": [0, 123, 131, 255],
    "orange": [250, 144, 62, 255],
    "white": [0, 0, 0, 0],
}

var customGroupsValue = [];
const CustomGroupCondition = {
    Source: {
        Tags: 1,
        Title: 2,
        Content: 3
    },
    Type: {
        Contains: 1,
        DoesntContain: 2
    }
}

var table;
var tableDataSource = [];

const TabRow = async (tab, tags = [], ner_tags = []) => {
    let group = {
        id: -1,
        title: "No group",
        color: tabGroupColor["white"]
    }
    if (tab.groupId != -1) {
        const groupObj = await chrome.tabGroups.get(tab.groupId);
        group = {
            id: tab.groupId,
            title: groupObj.title,
            color: tabGroupColor[groupObj.color]
        }
    }
    return {
        group: group,
        id: tab.id,
        checkbox: "",
        title: tab.title,
        tags: tags,
        ner_tags: ner_tags,
        removeTag(i) {
            this.tags.splice(i, 1);
            chrome.tabs.sendMessage(tab.id, {type: "set_tags", tags: this.tags});
        }
    };
}

const TableColumnsType = {
    group: {
        data: 'group'
    },
    id: {
        data: 'id'
    },
    checkbox: {
        title: '<label><input type="checkbox" class="select-all"/><span></span></label>',
        data: 'checkbox',
        render: (data, type, row) => {
            if (type === 'display') {
                return '<label><input type="checkbox" class="select-row" value="' + data + '"/><span></span></label>';
            }
            return data;
        }
    },
    title: {
        title: "Title",
        data: 'title',
        render: (data, type, row) => {
            if (type === 'display') {
                return `<a href="#" class="open-tab" data-tabid="${row.id}">${data}</a>`;
            }
            return data;
        }
    },
    tags: {
        title: "Tags",
        data: 'tags',
        render: (data, type, row) => {
            if (type === 'display') {
                if (data.length == 0) {
                    return `
                    <div class="preloader-wrapper small active">
                        <div class="spinner-layer spinner-yellow-only">
                            <div class="circle-clipper left">
                                <div class="circle"></div>
                            </div>
                            <div class="gap-patch">
                                <div class="circle"></div>
                            </div>
                            <div class="circle-clipper right">
                                <div class="circle"></div>
                            </div>
                        </div>
                    </div>
                    `;
                }
                return `<div class="chips tab-tags-chips" data-tabid="${row.id}"></div>`;
            }
            return data;
        }
    },
    ner_tags: {
        title: "NER Tags",
        data: 'ner_tags',
        render: (data, type, row) => {
            if (type === 'display') {
                return data.map((section) =>
                    `<label>${section.title}</label>` + arrayToChips(section.tags)
                ).join("<br>")
            }
            return data;
        }
    }
}

const tableColumns = [
    TableColumnsType.group,
    TableColumnsType.id,
    TableColumnsType.checkbox,
    TableColumnsType.title,
    TableColumnsType.tags,
    TableColumnsType.ner_tags
];

const escapeHtml = (unsafe) => {
    return unsafe.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
}

const arrayToChips = (arr, tabid) => {
    return arr.map((tag, i) => {
        return `<div class="chip">${escapeHtml(tag)}
                    <i class="close material-icons" data-tabid="${tabid}" data-tag="${i}">close</i>
                </div>`;
    }).join('')
}

const updateTabTags = async (tab) => {
    const contentResponse = await chrome.tabs.sendMessage(tab.id, {type: "tags"});
    let newData;
    if (contentResponse.type == "pageData") {
        const response = await fetch(serverUrl + "/tag", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(contentResponse)
        });
        const json = await response.json();
        chrome.tabs.sendMessage(tab.id, {type: "set_tags", tags: json.tags});
        newData = await TabRow(tab, json.tags, json.ner_tags);
    } else if (contentResponse.type == "tags") {
        newData = await TabRow(tab, contentResponse.tags, []);
    }
    const tabIndex = tableDataSource.findIndex((i) => i.id === tab.id)
    tableDataSource[tabIndex] = newData;
    table.row(tabIndex).data(newData).draw();
}

const updateTabsTable = async () => {
    const tabs = (await chrome.tabs.query({
        currentWindow: true
    })).filter((tab) => {
        return !tab.url.startsWith('chrome-extension://')
            && !tab.url.startsWith('devtools://')
            && !tab.url.startsWith('browser://')
            && !tab.url.startsWith('chrome://');
    });

    tableDataSource = await Promise.all(
        tabs.map(async (tab) => {
            return await TabRow(tab)
        }));

    tabs.forEach((tab) => {
        updateTabTags(tab);
    });

    table = $('#mainTable').DataTable({
        retrieve: true,
        searching: false,
        paging: false,
        info: false,
        ordering: false,
        columnDefs: [
            {
                targets: [
                    tableColumns.indexOf(TableColumnsType.group),
                    tableColumns.indexOf(TableColumnsType.id),
                    tableColumns.indexOf(TableColumnsType.ner_tags)
                ],
                visible: false,
            },
            {
                targets: [
                    tableColumns.indexOf(TableColumnsType.tags)
                ],
                width: "30%"
            },
            {
                targets: [
                    tableColumns.indexOf(TableColumnsType.ner_tags)
                ],
                width: "50%"
            }
        ],
        columns: tableColumns,
        data: tableDataSource,
        drawCallback: (settings) => {
            const api = settings.oInstance.api();
            const rows = api.rows({page: 'current'}).nodes();
            let last = null;

            api
                .column(tableColumns.indexOf(TableColumnsType.group), {page: 'current'})
                .data()
                .each((group, i) => {
                    if (last?.id !== group?.id) {
                        $(rows)
                            .eq(i)
                            .before(`<tr class="group" style="color: white; font-weight: 600; background:rgba(${group.color.join()})"><td colspan="6">${group.title}</td></tr>`);

                        last = group;
                    }
                });
        }
    });
    $("#mainTable")
        .on("draw.dt", () => {

            $('.chips.tab-tags-chips').each((i, el) => {
                $(el).chips({
                    data: tableDataSource[i].tags.map((tag) => {
                        return {tag: tag}
                    }),
                    onChipAdd: (parent, data) => {
                        tableDataSource[i].tags.push(data.firstChild.textContent);
                        chrome.tabs.sendMessage(parseInt($(parent).attr("data-tabid")), {
                            type: "set_tags",
                            tags: tableDataSource[i].tags
                        });
                    },
                    onChipDelete: (parent, data) => {
                        var index = tableDataSource[i].tags.indexOf(data.firstChild.textContent);
                        if (index !== -1) {
                            tableDataSource[i].tags.splice(index, 1);
                        }
                        chrome.tabs.sendMessage(parseInt($(parent).attr("data-tabid")), {
                            type: "set_tags",
                            tags: tableDataSource[i].tags
                        });
                    }
                });
            })
        })
    $('.select-all').prop('checked', false);
}

const groupTabs = async (groupsData) => {
    for (group of groupsData) {
        const tabGroupId = await chrome.tabs.group({
            tabIds: group.tabs
        });
        chrome.tabGroups.update(tabGroupId, {title: group.title})
    }
}

const loadCustomGroups = async function () {
    customGroupsValue = (await chrome.storage.local.get({"customGroups": []})).customGroups;
    for (group of customGroupsValue) {
        const groupEl = addCustomGroup(group.name);
        for (condition of group.conditions) {
            addCustomGroupCondition(groupEl, condition.source, condition.type, condition.value);
        }
    }
}

const saveCustomGroupsData = function () {
    customGroupsValue = $("#modal-custom-group>.modal-content>div.row>ul.collapsible>li").map((i, groupDiv) => {
        const name = $(groupDiv).find("div.collapsible-header input.group_name").val();
        const conditions = $(groupDiv).find("div.collapsible-body>div.row.condition").map((j, conditionDiv) => {
            return {
                source: parseInt($(conditionDiv).find("select.cond-source").val()),
                type: parseInt($(conditionDiv).find("select.cond-type").val()),
                value: $(conditionDiv).find("input.cond-value").val()
            };
        });
        return {
            name: name,
            conditions: conditions.get()
        }
    }).get();
    chrome.storage.local.set({customGroups: customGroupsValue});
}

const mergeIntersectedGroups = (groups) => {
    return groups.reduce((acc, group) => {
        let groupObj = structuredClone(group);
        acc.forEach((existingGroup, i) => {
            const intersectedTabs = group.tabs.filter((tab) => existingGroup.tabs.includes(tab));

            if (intersectedTabs.length > 0) {
                acc.push({
                    title: existingGroup.title + "+" + group.title,
                    tabs: intersectedTabs
                });

                existingGroup.tabs = existingGroup.tabs.filter((tab) => !intersectedTabs.includes(tab));
                groupObj.tabs = group.tabs.filter((tab) => !intersectedTabs.includes(tab));
                if (existingGroup.tabs.length == 0) {
                    acc.splice(i, 1);
                }
            }
        });

        if (groupObj.tabs.length > 0) {
            acc.push(groupObj);
        }

        return acc;
    }, []);
}

const customGrouping = async () => {
    const checkboxes = $(".select-row");
    const filteredDataSource = tableDataSource.filter((val, i) => {
        return checkboxes.get(i).checked
    });
    console.log("customGroupsValue")
    console.log(customGroupsValue)
    const groups = await Promise.all(customGroupsValue.map(async (group) => {
        const results = await Promise.all(filteredDataSource.map(async (tab, tabIndex) => {
            const tabContent = (await chrome.tabs.sendMessage(tab.id, {type: "content"})).content.toLowerCase();
            for (condition of group.conditions) {
                let source = "";
                switch (condition.source) {
                    case CustomGroupCondition.Source.Tags:
                        source = tab.tags;
                        break;
                    case CustomGroupCondition.Source.Title:
                        source = tab.title.toLowerCase();
                        break;
                    case CustomGroupCondition.Source.Content:
                        source = tabContent;
                        break;
                    default:
                        console.error("Wrong condition source", condition.source)
                        return false;
                }
                const sourceContainsValue = source.includes(condition.value.toLowerCase());
                if ((condition.type === CustomGroupCondition.Type.Contains) !== sourceContainsValue) {
                    return false;
                }
            }
            return true;
        }));
        const tabIds = filteredDataSource
            .filter((v, index) => results[index])
            .map((tab) => tab.id);
        return {
            title: group.name,
            tabs: tabIds
        }
    }));

    await groupTabs(mergeIntersectedGroups(groups));
}

const addCustomGroup = function (name = "") {
    const newElement = $(`
    <li>
        <div class="collapsible-header brown lighten-5">
            <div class="row valign-wrapper">
                <div class="input-field col s11">
                    <input placeholder="Group name" type="text" class="group_name" value="${name}">
                </div>
                <div class="col s1 right">
                    <i class="close material-icons group-remove">close</i>
                </div>
            </div>
        </div>
        <div class="collapsible-body" style="padding-top: 0 !important; padding-bottom: 0 !important;">
            <div class="row">
                <a href="#!" class="waves-effect brown darken-2 btn-small cond-add">
                    <i class="material-icons left">add</i>
                    Add rule</a>
            </div>
        </div>
    </li>
    `);

    $("#modal-custom-group .collapsible")
        .append(newElement);

    newElement.find("select").formSelect();

    return newElement;
}

const addCustomGroupCondition = function (
    groupDiv,
    condSource = CustomGroupCondition.Source.Tags,
    condType = CustomGroupCondition.Type.Contains,
    condValue = "") {
    const newElement = $(`
        <div class="row condition" style="margin-bottom: 0">
            <div class="input-field col s3">
                <select class="cond-source">
                    <option value="${CustomGroupCondition.Source.Tags}">Tags</option>
                    <option value="${CustomGroupCondition.Source.Title}">Title</option>
                    <option value="${CustomGroupCondition.Source.Content}">Content</option>
                </select>
            </div>
            <div class="input-field col s3">
                <select class="cond-type">
                    <option value="${CustomGroupCondition.Type.Contains}">contains</option>
                    <option value="${CustomGroupCondition.Type.DoesntContain}">doesn't contain</option>
                </select>
            </div>
            <div class="input-field col s5">
                <input id="cond-value" class="cond-value" type="text" value="${condValue}">
                <label for="cond-value">Value</label>
            </div>
            <div class="input-field col s1">
                <a href="#!" class="btn-flat waves-effect waves-green cond-remove"><i
                        class="close material-icons">close</i></a>
            </div>
        </div>
    `);
    newElement.find("select.cond-source").val(condSource);
    newElement.find("select.cond-type").val(condType);

    $(groupDiv).find("div.row:last").before(newElement);
    newElement.find("select").formSelect();

    return newElement;
}

const clusterGrouping = async () => {
    const checkboxes = $(".select-row");
    const filteredDataSource = tableDataSource.filter((val, i) => {
        return checkboxes.get(i).checked
    });

    const txts = await Promise.all(filteredDataSource.map(async (tab) => {
        if ($("#modal-cluster-group select.clustering-content").val() == "1") {
            const tabContent = (await chrome.tabs.sendMessage(tab.id, {type: "content"})).content
            return tabContent;
        } else {
            return tab.tags;
        }
    }));

    const response = await fetch(serverUrl + "/clustering", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            algorithm: $("#modal-cluster-group select.clustering-algorithm").val(),
            clusterCount: parseInt($("#modal-cluster-group #groups_amount").val()),
            txts: txts
        })
    })
    const json = await response.json()

    const groups = json.map((group) => {
        return {
            title: group.keywords.join(),
            tabs: group.docs_n.map((tabIndex) => filteredDataSource[tabIndex].id)
        }
    })
    await groupTabs(groups);
}

$(document).ready(async () => {
    $(".loader-mask").hide();
    $('.modal').modal();
    $('.collapsible.expandable').collapsible({
        accordion: false
    });
    $('select').formSelect();
    updateTabsTable();
    await loadCustomGroups();
    M.updateTextFields();
});

$("#cluster-group-button").click(async () => {
    $('.loader-mask').show();
    await clusterGrouping();
    await updateTabsTable();
    $(".loader-mask").hide();
});

$("#refresh").click(() => {
    updateTabsTable();
});

// $(document).on("click", '.remove-tag', (e) => {
// const target = $(e.target);
// const tabid = parseInt(target.attr("data-tabid"));
// const tagindex = parseInt(target.attr("data-tag"));
// const tabIndex = tableDataSource.findIndex((i) => i.id === tabid);
// tableDataSource[tabIndex].removeTag(tagindex);
// });

// Select all checkboxes when the "select all" checkbox is clicked
$(document).on("click", '.select-all', (e) => {
    $('.select-row').prop('checked', e.target.checked);
    if (e.target.checked) {
        $("a.grouping-button").removeClass("disabled");
    } else {
        $("a.grouping-button").addClass("disabled");
    }
});


$(document).on('change', '.clustering-algorithm', (e) => {
    if ($('.clustering-algorithm :selected').text() === 'OPTICS') {
        $('.groups_amount_div').hide();
    } else {
        $('.groups_amount_div').show();
    }


});

var lastCheckedIndex = -1;
$(document).on("click", '.select-row', (e) => {
    if (e.target.checked) {
        const currentIndex = $(e.target).index(".select-row");
        if (lastCheckedIndex >= 0 && e.shiftKey) {
            $(".select-row").slice(
                Math.min(currentIndex, lastCheckedIndex),
                Math.max(currentIndex, lastCheckedIndex)
            ).prop('checked', true);
        }
        $("a.grouping-button").removeClass("disabled");
        lastCheckedIndex = currentIndex;
    } else {
        $('.select-all').prop('checked', false);
        lastCheckedIndex = -1;
        if ($(".select-row:checked").length == 0) {
            $("a.grouping-button").addClass("disabled");
        }
    }
});

$(document).on("click", 'a.open-tab', (e) => {
    const tabid = parseInt($(e.target).attr("data-tabid"))
    chrome.tabs.update(tabid, {
        active: true
    })
});

/* Custom grouping modal */

$("#custom-add-group").click((e) => {
    console.log("addCustomGroup")
    addCustomGroup();
    saveCustomGroupsData();
});

$("#modal-custom-group").on("click", '.group-remove', (e) => {
    $(e.target).parents("li").remove();
    saveCustomGroupsData();
});

$("#modal-custom-group").on("click", '.cond-add', (e) => {
    addCustomGroupCondition($(e.target).parent().parent().parent());
    saveCustomGroupsData();
});

$("#modal-custom-group").on("click", '.cond-remove', (e) => {
    $(e.target).parents(".row").first().remove();
    saveCustomGroupsData();
});

$("#modal-custom-group").on("focusout", "input, select", (e) => {
    saveCustomGroupsData();
});

$("#custom-group-button").click(async () => {
    $(".loader-mask").show();
    await customGrouping();
    await updateTabsTable();
    $(".loader-mask").hide();
});

$(document).ready(function () {
    $('.collapsible').collapsible();
});