kimchi.report_add_main = function() {
    var generateReportName = function() {
        return 'report-' + new Date().getTime();
    };

    var addReportForm = $('#form-report-add');
    var submitButton = $('#button-report-add');
    var nameTextbox = $('input[name="name"]', addReportForm);
    var errorMessage = $('#report-error-message');
    var submitForm = function(event) {
        if(submitButton.prop('disabled')) {
            return false;
        }
        var reportName = nameTextbox.val() || generateReportName();
        nameTextbox.val(reportName);
        var formData = addReportForm.serializeObject();
        errorMessage.text('');
        submitButton
            .text(i18n['msg.host.debugreport.generating'])
            .prop('disabled', true);
        nameTextbox.prop('disabled', true);
        kimchi.createReport(formData, function(result) {
            kimchi.window.close();
            kimchi.topic('kimchi/debugReportAdded').publish({
                result: result
            });
        }, function(result) {
            result && result['message'] &&
                $('#report-error-message').text(result['message']);
            submitButton
                .text(i18n['msg.host.debugreport.generate'])
                .prop('disabled', false);
            nameTextbox.prop('disabled', false).focus();
        });

        event.preventDefault();
    };

    addReportForm.on('submit', submitForm);
    submitButton.on('click', submitForm);
};
