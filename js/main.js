/*
 * Project Burnet
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Anthony Liguori <aliguori@us.ibm.com>
 *
 * All Rights Reserved.
 */

function genTile(title, image, gray, small)
{
    var html = "";
    var style = "icon";

    if (gray) {
        style += " stopped";
    }

    if (small) {
        style += " small";
    }

    html += "<div class=\"" + style + "\">\n";
    html += "<img src=\"" + image + "\"/>\n";
    html += "<h3>" + title + "</h3></a>\n";
    html += "</div>";

    return html;
}

function genPeer(name)
{
    return "<li class=\"project\"><a href=\"#\" title=\"titi\">titi</a></li>";
}

function load(data)
{
    var html = "";
    var i;

    for (i = 0; i < data.vms.length; i++) {
        html += genTile(data.vms[i].name, data.vms[i].image, !data.vms[i].running, false);
    }
    $("#vms").append(html);

    html = "";
    for (i = 0; i < data.templates.length; i++) {
        html += genTile(data.templates[i].name, data.templates[i].image, false, true);
    }
    $("#templates").prepend(html);

    html = "";
    for (i = 0; i < data.peers.length; i++) {
	html += genPeer(data.peers[i]);
    }
    $("ul.projects").append(html);

    $("div.icon").draggable({ revert: true });
}

function start()
{
    var html = "";

    html += genTile("Create New Templates from ISOS", "images/image-missing.svg", false, true);
    html += genTile("Create New Template from Guests", "images/image-missing.svg", false, true);
    $("#templates").append(html);

    html = genTile("Create Guest", "images/image-missing.svg", false, true);
    $("#custom").append(html);

    $.ajax({
	url: "rest/guests",
	dataType: "json"
    }).done(load);

    $(".btn").button();
}

$(document).ready(function(){ start(); });
