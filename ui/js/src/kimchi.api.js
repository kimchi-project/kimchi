/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Hongliang Wang <hlwanghl@cn.ibm.com>
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
var kimchi = {

	url : "../../../",

	/**
	 *
	 * Create a new Virtual Machine. Usage: kimchi.createVM({ name: 'MyUbuntu',
	 * template: '/templates/ubuntu_base' }, creationSuc, creationErr);
	 *
	 * settings: name *(optional)*: The name of the VM. Used to identify the VM
	 * in this API. If omitted, a name will be chosen based on the template
	 * used. template: The URI of a Template to use when building the VM
	 * storagepool *(optional)*: Assign a specific Storage Pool to the new VM
	 * suc: callback if succeed err: callback if failed
	 */
	createVM : function(settings, suc, err) {
		$.ajax({
			url : "/vms",
			type : "POST",
			contentType : "application/json",
			data : JSON.stringify(settings),
			dataType : "json"
		}).done(suc).fail(err);
	},

	/**
	 *
	 * Create a new Template. settings name: The name of the Template. Used to
	 * identify the Template in this API suc: callback if succeed err: callback
	 * if failed
	 */
	createTemplate : function(settings, suc, err) {
		$.ajax({
			url : "/templates",
			type : "POST",
			contentType : "application/json",
			data : JSON.stringify(settings),
			dataType : "json"
		}).done(suc).fail(err);
	},

	deleteTemplate : function(tem, suc, err) {
		$.ajax({
			url : kimchi.url + 'templates/' + tem,
			type : 'DELETE',
			contentType : 'application/json',
			dataType : 'json',
			success : suc,
			error : err
		});
	},

	listTemplates : function(suc, err) {
		$.ajax({
			url : kimchi.url + 'templates',
			type : 'GET',
			contentType : 'application/json',
			dataType : 'json',
			success : suc,
			error : err
		});
	},

	/**
	 * Retrieve the information of a template by the given name.
	 */
	retrieveTemplate : function(templateName, suc, err) {
                $.ajax({
                        url : kimchi.url + "templates/" + templateName,
                        type : 'GET',
                        contentType : 'application/json',
                        dataType : 'json'
                }).done(suc);
        },

	/**
	 * Update a template with new information.
	 * TODO: Update me when the RESTful API is available.
	 * Now work it around by remove the template and then
	 * recreate it with new information.
	 */
	updateTemplate : function(name, settings, suc, err) {
		kimchi.retrieveTemplate(name, function(template) {
			$.extend(template, settings);
			kimchi.deleteTemplate(name, function() {
				kimchi.createTemplate(template, suc, err);
			}, err);
		}, err);
	},

	/**
	 * Create a new Storage Pool. settings name: The name of the Storage Pool
	 * path: The path of the defined Storage Pool type: The type of the defined
	 * Storage Pool capacity: The total space which can be used to store volumes
	 * The unit is MBytes suc: callback if succeed err: callback if failed
	 */
	createStoragePool : function(settings, suc, err) {
		$.ajax({
			url : '/storagepools',
			type : 'POST',
			contentType : 'application/json',
			data : JSON.stringify(settings),
			dataType : 'json'
		}).done(suc).fail(err);
	},

	startVM : function(vm, suc, err) {
		$.ajax({
			url : kimchi.url + 'vms/' + vm + '/start',
			type : 'POST',
			contentType : 'application/json',
			dataType : 'json',
			success : suc,
			error : err
		});
	},

	stopVM : function(vm, suc, err) {
		$.ajax({
			url : kimchi.url + 'vms/' + vm + '/stop',
			type : 'POST',
			contentType : 'application/json',
			dataType : 'json',
			success : suc,
			error : err
		});
	},

	resetVM : function(vm, suc, err) {
		$.ajax({
			url : kimchi.url + 'vms/' + vm + '/stop',
			type : 'POST',
			contentType : 'application/json',
			dataType : 'json',
			success : function() {
				$.ajax({
					url : kimchi.url + 'vms/' + vm + '/start',
					type : 'POST',
					contentType : 'application/json',
					dataType : 'json',
					success : suc,
					error : err
				});
			},
			error : err
		});
	},

	deleteVM : function(vm, suc, err) {
		$.ajax({
			url : kimchi.url + 'vms/' + vm,
			type : 'DELETE',
			contentType : 'application/json',
			dataType : 'json',
			success : suc,
			error : err
		});
	},

	vncToVM : function(vm) {
		$.ajax({
			url : "/vms/" + vm + "/connect",
			type : "POST",
			dataType : "json",
		}).done(function(data, textStatus, xhr) {
			url = "/vnc_auto.html?port=" + data.graphics.port;
			window.open(url);
		});
	},

	listVMs : function(suc, err) {
		$.ajax({
			url : kimchi.url + 'vms',
			type : 'GET',
			contentType : 'application/json',
			dataType : 'json',
			success : suc,
			error : err
		});
	},

	listTemplates : function(suc, err) {
		$.ajax({
			url : kimchi.url + 'templates',
			type : 'GET',
			contentType : 'application/json',
			dataType : 'json',
			success : suc,
			error : err
		});
	},

	listStoragePools : function(suc, err) {
		$.ajax({
			url : kimchi.url + 'storagepools',
			type : 'GET',
			contentType : 'application/json',
			dataType : 'json',
			success : suc,
			error : err
		});
	}

};
