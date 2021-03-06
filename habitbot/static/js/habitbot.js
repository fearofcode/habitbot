$(document).ready(function() {

    // http://stackoverflow.com/questions/37684/how-to-replace-plain-urls-with-links
    function linkify(inputText) {
        var replacedText, replacePattern1, replacePattern2, replacePattern3;

        //URLs starting with http://, https://, or ftp://
        replacePattern1 = /(\b(https?|ftp):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/gim;
        replacedText = inputText.replace(replacePattern1, '<a href="$1">$1</a>');

        //URLs starting with "www." (without // before it, or it'd re-link the ones done above).
        replacePattern2 = /(^|[^\/])(www\.[\S]+(\b|$))/gim;
        replacedText = replacedText.replace(replacePattern2, '$1<a href="http://$2">$2</a>');

        //Change email addresses to mailto:: links.
        replacePattern3 = /(\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,6})/gim;
        replacedText = replacedText.replace(replacePattern3, '<a href="mailto:$1">$1</a>');

        return replacedText;
    }

    $(".goaltext").each(function() {
        var text = $(this).text();
        $(this).html(linkify(text));
    })

    $(".checkbox").hover(
        function() {
            $(this).children(".skip").css('display','inline');
        },
        function() {
            $(this).children(".skip").hide();
        }
    );

    $('#streak-tab a').click(function (e) {
      e.preventDefault();
      $(this).tab('show');
    })
});

