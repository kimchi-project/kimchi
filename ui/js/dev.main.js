/*
 * Project Burnet
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Anthony Liguori <aliguori@us.ibm.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

function genTile(title, image, gray, small, folder)
{
    var html = "";
    var style = "icon";

    if (gray) {
        style += " stopped";
    }

    if (small) {
        style += " small";
    }

    if (folder) {
        style += " folder";
    }

    visible = "active";

    html += "<div class=\"" + style + "\" id=\"" + title + "\">\n";
    html += "<img class=\"" + visible + "\" src=\"" + image + "\"/>\n";
    html += "<h3>" + title + "</h3></a>\n";
    html += "</div>";

    return html;
}

function genPeer(name)
{
    return "<li class=\"project\"><a href=\"#\" title=\"titi\">titi</a></li>";
}

function selectIcon(node)
{
    if (node.className.indexOf("selected") == -1) {
        node.className = node.className + " selected"
    } else {
        node.className = node.className.replace(/selected/g, "")
    }
}

function load_image(src, name)
{
    var newImage = new Image();

    newImage.onload = function(){
        old_pic = $("#"+name+' img');
        new_pic = $('<img src="' + src + '"/>');
        old_pic.after(new_pic);
        old_pic.remove();
        new_pic.addClass('active');
    }
    newImage.src = src;
}

function getCurrentImgs()
{
    var curImgs = new Object();
    var activeImgs = $("img.active");

    activeImgs.each(function(){
        curImgs[$(this).parent().attr('id')] = $(this).attr('src');
    });
    return curImgs;
}

function load_vms(data)
{
    var sel_vms;
    var html = "";
    var i;

    sel_vms = getSelectedItems("vms");
    active_imgs = getCurrentImgs();

    $("#vms").empty();
    for (i = 0; i < data.length; i++) {
        var image;
        if (data[i].state == 'running') {
            image = data[i].screenshot;
        } else {
            image = data[i].icon;
        }
        if (!image) {
            image = "images/icon-vm.svg";
        }
        old_img = active_imgs[data[i].name];
        html = genTile(data[i].name, old_img ? old_img : image,
                       data[i].state != 'running', false);
        $("#vms").append(html);
        load_image(image, data[i].name);
    }
    selectItems("vms", sel_vms);

    $("#vms .icon").click(function() {
        selectIcon(this);
        updateVMToolbar();
    });
}

function updateVMToolbar()
{
    selectedVMs = getSelectedItems("vms")
    toolbar = $("#vm-toolbar > li > a")

    if (selectedVMs.length > 1) {
        for (i = 0; i < toolbar.length; i++) {
            toolbar[i].className = toolbar[i].className + " disabled"
        }

        $(".icon-play").removeClass("disabled")
        $(".icon-off").removeClass("disabled")

        return
    }

    if (selectedVMs.length <= 1) {
        for (i = 0; i < toolbar.length; i++) {
            toolbar[i].className = toolbar[i].className.replace(/disabled/g, "")
        }
    }

    if (selectedVMs.length == 1) {
        if ($("#" + selectedVMs[0]).hasClass("stopped")) {
            $(".icon-desktop").addClass("disabled")
        }
        else {
            $(".icon-desktop").removeClass("disabled")
        }
    }
}

function load_templates(data)
{

    var paths = []
    var hidden = []
    var folders = []
    var html = "";
    var i;
    var j;

    sel_templates = getSelectedItems("templates");
    $("#templates").empty();

    // get all bread-crumbs paths
    breadcrumbs = $("#breadcrumbs > li > a")
    for (i = 1; i < breadcrumbs.length; i++) {
        paths.push(breadcrumbs[i].textContent)
    }

    for (i = 0; i < data.length; i++) {
        folder = data[i].folder

        // verify which templates are in the current path
        for (j = 0; j < paths.length; j++ ) {

            // first path matched: shift to the next one
            if (folder[0] == paths[j]) {
                folder.shift()
            } else {
                // template not in current folder view: hide it
                hidden.push(data[i].name)
                break;
            }
        }

        // template must be hidden: do not show it
        if ($.inArray(data[i].name, hidden) != -1) {
            continue
        }

        // folder field is empty: display template
        if (folder.length == 0) {
            html += genTile(data[i].name, data[i].icon, false, true, false);
            continue
        }

        // folder still not displayed: show it
        if ($.inArray(folder[0], folders) == -1) {
            folders.push(folder[0])
            html += genTile(folder[0], "images/gtk-directory.svg", false, true, true);
        }
    }

    $("#templates").append(html);
    selectItems("templates", sel_templates)
}

function updateTemplatesView()
{
    $.ajax({
        url: "/templates",
        dataType: "json"
    }).done(load_templates);
}

function load_peers(data)
{
    var html = "";
    var i;

    $("ul.projects").empty();
    for (i = 0; i < data.length; i++) {
        html += genPeer(data[i]);
    }
    $("ul.projects").append(html);
}

function load(data)
{
    console.log("load");
    $.ajax({
	url: "/vms",
	dataType: "json"
    }).done(load_vms);

    $.ajax({
	url: "/templates",
	dataType: "json"
    }).done(load_templates);

    $.ajax({
    url: "/peers",
    dataType: "json",
    }).done(load_peers);

    $("div.icon").draggable({ revert: true });

    window.setTimeout("load();", 5000);
}

function init_lang_select()
{
    var lang = $("html").attr("lang")
    $("#localLang").val(lang)
}

function getSelectedItems(id)
{
    var names = []
    var items = document.getElementById(id);
    var selectedItems = items.getElementsByClassName("selected");

    for (i = 0; i < selectedItems.length; i++) {
        names[i] = selectedItems[i].id;
    }

    return names;
}

function selectItems(id, names)
{
    var icons = $("#" + id + " .icon");
    var i;

    for (i = 0; i < icons.length; i++) {
        var id = icons[i].id;
        if (names.indexOf(id) >= 0) {
            icons[i].className = icons[i].className + " selected";
        }
    }
}

function deselectIcons(names)
{
    for (i = 0; i < names.length; i++) {
        $("#" + names[i]).removeClass("selected")
    }
}

function deleteSelectedItems(Collection)
{
    $("#dialog-delete-" + Collection + "-confirm").dialog({
       resizable: false,
       height:220,
       modal: true,
       buttons: {
           "Delete": function() {
               item = getSelectedItems(Collection);
               for (i = 0; i < item.length; i++) {
                   $.ajax({
                       url: "/" + Collection + "/" + item[i],
                       type: "DELETE",
                       context: document.getElementById(item[i])
                   }).done(function(data, textStatus, context) {
                       $("#" + $(this).context.id).remove();
                   }).fail(function(context) {
                       alert("Failed to delete " + $(this).context.id);
                   });
               }
               $(this).dialog("close");
           },
           Cancel: function() {
               $(this).dialog("close");
           }
       }
    });
}

function start()
{
    var html = "";

    html = genTile("Create Guest", "images/image-missing.svg", false, true);
    $("#custom").append(html);

    load();
    init_lang_select();

    $("#vm-toolbar .icon-play").click(function() {
        vms = getSelectedItems("vms");

        for (i = 0; i < vms.length; i++) {
            $.ajax({
                url: "/vms/" + vms[i]  + "/start",
                type: "POST",
                dataType: "json",
                context: document.getElementById(vms[i]),
            }).complete(function(context, status) {
                updateVMToolbar();

                if (status == "success") {
                    vm = $(this).context
                    vm.className = vm.className.replace(/stopped/g, "");
                } else {
                    alert ("Failed to start " + $(this).context.id);
                }
            });
        }

        deselectIcons(vms)
    });

    $("#vm-toolbar .icon-off").click(function() {
        vms = getSelectedItems("vms");

        for (i = 0; i < vms.length; i++) {
            $.ajax({
                url: "/vms/" + vms[i]  + "/stop",
                type: "POST",
                dataType: "json",
                context: document.getElementById(vms[i]),
            }).complete(function(context, status) {
                updateVMToolbar();

                if (status == "success") {
                    vm = $(this).context
                    vm.className = vm.className + " stopped"
                } else {
                    alert ("Failed to power off " + $(this).context.id);
                }
            });
        }

        deselectIcons(vms)
    });

    $(".icon-desktop").click(function() {
        if ($(this).hasClass("disabled")) {
            return
        }

        vm = getSelectedItems("vms");

        $.ajax({
            url: "/vms/" + vm[0]  + "/connect",
            type: "POST",
            dataType: "json",
        }).done(function(data, textStatus, xhr) {
            url = "/vnc_auto.html?port=" + data.vnc_port + "&logging=debug"
            popup = window.open(url, "", "target=_blank,height=600,width=800,scrollbars=1");
            if (popup) {
                popup.focus()
            } else {
                alert("A popup blocker may have prevented the console from displaying properly.")
            }
        });

        deselectIcons(vm)
    });

    $("#vm-toolbar .icon-trash").click(function() {
        deleteSelectedItems('vms')
    });

    $("#template-toolbar .icon-plus").click(function() {
        templates = getSelectedItems("templates");
        if (templates.length != 1) {
            return;
        }
        var req = {"template": "/templates/" + templates[0]};
        $.ajax({
            url: "/vms",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify(req),
            dataType: "json",
            context: document.getElementById(templates[0]),
        }).done(function() {
            $.ajax({
                url: "/vms",
                dataType: "json"
            }).done(load_vms);
        }).fail(function(context) {
            alert("Failed to create VM from Template: " + $(this).context.id);
        });
    });

    $("#template-toolbar .icon-trash").click(function() {
        deleteSelectedItems('templates')
    });
    // enable selection for templates
    $("#templates").on("click", ":not(.folder)", function() {
        selectIcon(this);
    });

    // handle click in template folder
    $("#templates").on("click", ".folder", function() {
        name = $(this).attr("id")

        html = "<li><a class=\"icon-angle-right\">" + name  + "</a></li>"
        $("#breadcrumbs").append(html)

        updateTemplatesView();
    });

    // handle click in bread-crumbs fields
    $("#breadcrumbs").on("click", "li", function() {
        // remove all next siblings and update templates view
        $(this).nextAll().remove();
        updateTemplatesView();
    });

    $(".btn").button();
    $('#localLang').change(function() {
        var selection = $('#localLang option:selected').val();
        document.cookie = 'burnetLang' + "=" + selection;
        window.location.reload()
    });
}

$(document).ready(function(){ start(); });
