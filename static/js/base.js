/**
 *
 * Copyright 2022, Institute for Systems Biology
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */

require.config({
    baseUrl: STATIC_FILES_URL+'js/',
    paths: {
        jquery: 'lib/jquery-3.6.0.min',
        bootstrap: 'lib/bootstrap.min',
        utils: 'utils',
        session_security: 'session_security/script',
        tippy: 'lib/tippy-bundle.umd.min',
        '@popperjs/core': 'lib/popper.min'
    },
    shim: {
        '@popperjs/core': {
            exports: "@popperjs/core"
        },
        'tippy': {
            exports: 'tippy',
            deps: ['@popperjs/core']
        },
        'bootstrap': ['jquery', '@popperjs/core'],
        'session_security': ['jquery'],
        'utils': ['jquery', 'bootstrap']
    }
});

// Set up common JS UI actions which span most views
require([
    'jquery',
    'utils',
    'bootstrap',
    'session_security',
], function($, utils, bootstrap) {
    'use strict';

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    };

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            let csrftoken = $.getCookie('csrftoken');
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    $.createMessage = function(message, messageType) {
        var message_obj = $('<div class="row">' +
            '<div class="col-lg-12">' +
            '<div class="alert alert-'+messageType+' alert-dismissible">' +
            '<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>'
            + message + '</div></div></div>');
        message_obj.prependTo('main > .container');
    };

    $(document).ready(function(){
        if(sessionStorage.getItem("reloadMsg")) {
            var msg = JSON.parse(sessionStorage.getItem("reloadMsg"));
            utils.showJsMessage(msg.type,msg.text,true);
        }
        sessionStorage.removeItem("reloadMsg");
    });

    // Per https://stackoverflow.com/questions/13550477/twitter-bootstrap-alert-message-close-and-open-again
    // Set up our own data-hide type to 'hide' our alerts instead of popping them off the DOM entirely
    $("[data-hide]").on("click", function(){
        $(this).closest("." + $(this).attr("data-hide")).hide();
    });

    if(user_is_auth) {
        let sessionSecurity = new yourlabs.SessionSecurity({
            pingUrl: pingUrl,
            warnAfter: warnAfter,
            expireAfter: expireAfter,
            confirmFormDiscard: confirmFormDiscard,
            returnToUrl: BASE_URL
        });
    }

    $('#gov_warning button').on('click', function(){
        $('#gov_warning button').prop("disabled", true);
        $('#gov_warning').modal('hide');
        $.ajax({
            async: true,
            type: "GET",
            url: "/warning/",
            contentType: "charset=utf-8",
            fail: function () {
                console.warn("Unable to record status for Government Notice! You may see that popup again.");
            },
            always: function() {
                $('#gov_warning button').prop("disabled", false);
            }
        });
    });

    if(!warningSeen && showWarning) {
        $('#gov_warning').modal('show');
    }

    $('#body').on('click', '.external-link', function(){
        let url = $(this).attr('url');
        $('#go-to-external-link').attr('href', url);
    });

    $('#go-to-external-link').on('click', function() {
        $('#external-web-warning').modal('hide');
    });

    $('#body').on('click', '.copy-this', function(){
        let content = $(this).attr('content');
        navigator.permissions.query({name: "clipboard-write"}).then(result => {
            if (result.state == "granted" || result.state == "prompt") {
                navigator.clipboard.writeText(content);
            } else  {
                console.debug("Failed to access clipboard!");
            }
        });
    });

    $('.btn-reset').on("click", function () {
        let reset_target = $($(this).data('target'));
        reset_target.find('input:checkbox').prop('checked', false);
        reset_target.find('input:radio').prop('checked', false);
        reset_target.find('input[type="number"]').each(function(){
            $(this).val($(this).prop('defaultValue'));
        });
        reset_target.find('input').not(':hidden').first().trigger('change');
    });

    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
});

// Return an object for consts/methods used by most views
define('base', ['jquery', 'utils'], function($, utils) {

    // Resets forms in modals on hide. Suppressed warning when leaving page with dirty forms
    $('.modal').on('hide.bs.modal', function () {
        if(!$(this).prop("saving")) {
            if($(this).find('form').get().length) {
                $(this).find('form').get(0).reset();
            }
        }
    });

    $.getCookie = utils.getCookie;
    $.setCookie = utils.setCookie;
    $.removeCookie = utils.removeCookie;

    return {
        // blacklist: /[^\w]/g,
        // From http://www.regular-expressions.info/email.html
        email: /^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/,
        showJsMessage: utils.showJsMessage,
        // Simple method for standardizing storage of a message into sessionStorage so it can be retrieved and reloaded
        // at document load time
        setReloadMsg: function(type,text) {
            sessionStorage.setItem("reloadMsg",JSON.stringify({type: type, text: text}));
        },
        setCookie: function(name,val,expires_in,path) {
            utils.setCookie(name,val,expires_in,path);
        },
        removeCookie: function(name, path) {
            utils.removeCookie(name, path);
        },
        blockResubmit: utils.blockResubmit
    };


});

let numberWithCommas = function (num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
};

let is_input_valid = function (e) {
    $('#alert_message').html('');
    let search_title = $('#search-save-title').val();
    if (search_title.match(/\s/)) {
        $('#alert_message').html('<i class="fa-solid fa-circle-exclamation"></i> ' + 'No space character is allowed. Please revise the search title.');
        e.preventDefault();
        return false;
    }

    let invalid_chars = search_title.match(/[^\w]/g);
    if (invalid_chars) {
        let invalid_chars_list_str = Array.from(new Set(invalid_chars)).join(', ')
        $('#alert_message').html('<i class="fa-solid fa-circle-exclamation"></i> ' + 'Your search title contains invalid characters (<span class="fw-bold">' + invalid_chars_list_str + '</span>). Please choose another search title.');
        e.preventDefault();
        return false;
    }
    return true;
};