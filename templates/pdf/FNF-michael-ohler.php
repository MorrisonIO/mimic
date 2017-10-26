
<!DOCTYPE html>
<!-- saved from url=(0052)http://13.58.114.203/media/templates/pdf/page_4.html -->
<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">

    <title>FRAME</title>
    <style>
        @font-face {
            font-family: 'nexa_boldregular';
            src: url('/media/brochure_staff/Michael-Ohler-FNF-assests/fonts/nexa_bold-webfont.woff2') format('woff2'),
                 url('/media/brochure_staff/Michael-Ohler-FNF-assests/fonts/nexa_bold-webfont.woff') format('woff');
/*            src: url('./Michael-Ohler-FNF-assests/fonts/nexa_bold-webfont.woff2') format('woff2'),
                 url('./Michael-Ohler-FNF-assests/fonts/nexa_bold-webfont.woff') format('woff');*/
            font-weight: normal;
            font-style: normal;

        }
        @font-face {
            font-family: 'nexa_lightregular';
            src: url('/media/brochure_staff/Michael-Ohler-FNF-assests/fonts/nexa_light-webfont.woff2') format('woff2'),
                 url('/media/brochure_staff/Michael-Ohler-FNF-assests/fonts/nexa_light-webfont.woff') format('woff');
/*            src: url('./Michael-Ohler-FNF-assests/fonts/nexa_light-webfont.woff2') format('woff2'),
                 url('./Michael-Ohler-FNF-assests/fonts/nexa_light-webfont.woff') format('woff');*/
            font-weight: normal;
            font-style: normal;

        }
        @font-face {
            font-family: 'nexa_regularregular';
/*            src: url('./Michael-Ohler-FNF-assests/fonts/nexaregular-webfont.woff2') format('woff2'),
                 url('./Michael-Ohler-FNF-assests/fonts/nexaregular-webfont.woff') format('woff');*/
            src: url('/media/brochure_staff/Michael-Ohler-FNF-assests/fonts/nexaregular-webfont.woff2') format('woff2'),
                 url('/media/brochure_staff/Michael-Ohler-FNF-assests/fonts/nexaregular-webfont.woff') format('woff');
            font-weight: normal;
            font-style: normal;

        }
        @page {
            size: portrait;
            width: 88.9mm;
            height: 50.8mm;
            margin: 0;
            padding: 0;
        }
        input, textarea {
            border: none;
        }
        img {
            width: 100%;
            height: auto;
        }
        .template-content {
            position: relative;
            width: 88.9mm;
            height: 50.8mm;
            margin: 0;
            padding: 0;
        }
/*        .img-hor {
            -moz-transform: scaleX(-1);
            -o-transform: scaleX(-1);
            -webkit-transform: scaleX(-1);
            transform: scaleX(-1);
            filter: FlipH;
            -ms-filter: "FlipH";
        }

        .img-vert {
                -moz-transform: scaleY(-1);
                -o-transform: scaleY(-1);
                -webkit-transform: scaleY(-1);
                transform: scaleY(-1);
                filter: FlipV;
                -ms-filter: "FlipV";
        }

        .img-hor-vert {
                -moz-transform: scaleX(-1);
                -o-transform: scaleX(-1);
                -webkit-transform: scaleX(-1);
                transform: scaleX(-1);
                filter: FlipH;
                -ms-filter: "FlipH";
            
                -moz-transform: scaleY(-1);
                -o-transform: scaleY(-1);
                -webkit-transform: scaleY(-1);
                transform: scaleY(-1);
                filter: FlipV;
                -ms-filter: "FlipV";
        }*/
        .flip-vertical {
/*            -moz-transform: scale(1, -1);
            -webkit-transform: scale(1, -1);
            -o-transform: scale(1, -1);
            transform: scale(1, -1);
            filter: FlipV;
            -ms-filter: "FlipV";*/

            -moz-transform: scaleY(-1);
            -o-transform: scaleY(-1);
            -webkit-transform: scaleY(-1);
            transform: scaleY(-1);
            filter: FlipV;
            -ms-filter: "FlipV";
        }
        
        .flip-horizontal {
            -moz-transform: scale(-1, 1);
            -webkit-transform: scale(-1, 1);
            -o-transform: scale(-1, 1);
            transform: scale(-1, 1);
            filter: FlipH;
            -ms-filter: "FlipH";
        }
        
        .template-page {
            width: 88.9mm;
            height: 50.8mm;
            position: relative;
            page-break-after: always;
        }
        .michael-bg-x {
            background-image: url('/media/brochure_staff/Michael-Ohler-FNF-assests/images/Michael-Ohler-FNF--bg-invert.jpg');
            background-image: url('/media/brochure_staff/Michael-Ohler-FNF-assests/images/Michael-Ohler-FNF--bg.jpg');
/*            background-image: url('./Michael-Ohler-FNF-assests/images/Michael-Ohler-FNF--bg-invert.jpg');
            background-image: url('./Michael-Ohler-FNF-assests/images/Michael-Ohler-FNF--bg.jpg');*/
            background-size: cover;
            background-repeat: no-repeat;
        }
        .logo-1 {
            position: absolute;
            top: 6.4mm;
            width: 51.3mm;
        }
        .logo-2 {
            position: absolute;
            top: 36.4mm;
            right: 6.3mm;
            width: 32.2mm;
        }
        
        @media print {
            html,
            body {
                size: portrait;
                width: 88.9mm;
                height: 50.8mm;
                margin: 0;
                padding: 0;
            }
            * {
                box-sizing: border-box;
                -moz-box-sizing: border-box;
            }
            .template-page {
                size: landscape;
                page-break-after: always;
            }
        }
        .absolute {
            position: absolute;
        }
        .left-align {
            left:25px;
        }
        .color-1 {
            color: #15284a; blue 
        }
        .color-2 {
            color: #a7a9ac;/* grey */
        }
        .color-3 {
            color: #bf302c;
        }
        .size-0 {
            font-size: 12.5px;
            margin: 0;
        }
        .size-1 {
            font-size: 9.7px;
            margin: 0;
        }
        .size-2 {
            font-size: 9.7px;
            margin: 0;
        }
        .font-0 {
            font-family: 'nexa_lightregular';
            font-weight: normal;
            font-style: normal;
        }
        .font-1 {
            font-family: 'nexa_regularregular';
            font-weight: normal;
            font-style: normal;
        }
        .font-2 {
            font-family: 'nexa_boldregular';
            font-weight: normal;
            font-style: normal;
        }
        .kind {
            margin-right: 1mm;
        }
        .name {
            top:20.7mm;
        }
        .position {
            top:24.8mm;
            text-transform: uppercase;
        }
        .position2 {
            top:27.7mm;
            text-transform: uppercase;
        }
        .office {
            top:33.9mm;
        }
        .cell {
            top:32.4mm;
        }
        .fax {
            top:35.8mm;
        }
        .email {
            top:37.3mm;
        }
        .web {
            top: 40.3mm;
        }
        .placeholder:empty::before {
            content: attr(data-placeholder);
        }
    span.kind {
            display: inline-block;
            width: 5px;
        }

    </style>
</head>

<body>
    <div class="template-pages">
        <div class="template-page michael-bg">

            <div class="template-content">
                <div class="logo-1 left-align">
                    <img class="temp-img" alt="logo" src="/media/brochure_staff/Michael-Ohler-FNF-assests/images/logo.png">
                </div>
                <div class="text-block">
                        {% if not context %}
                            <p class="absolute size-0 font-2 left-align color-1 placeholder name" data-placeholder="Full Name">Full Name</p>
                            <p class="absolute size-1 font-2 left-align color-2 placeholder txt-upper position" data-placeholder="Position">Position</p>
                            <p class="absolute size-1 font-2 left-align color-2 placeholder txt-upper position2" data-placeholder="Department">Department</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 office" data-placeholder="Cell Phone"><span class="kind color-1">t</span>Cell Phone</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 email" data-placeholder="E-mail"><span class="kind color-1">e</span>E-mail</p>
                            <p class="absolute size-2 font-2 left-align color-1 placeholder txt-15 web" data-placeholder="Web Address">Web Address</p>
                      {% else %}
                            <p class="absolute size-0 font-2 left-align color-1 placeholder name" data-placeholder="Full Name">{{context.full_name}}</p>
                            <p class="absolute size-1 font-2 left-align color-2 placeholder txt-upper position" data-placeholder="Position">{{context.position}}</p>
                            <p class="absolute size-1 font-2 left-align color-2 placeholder txt-upper position2" data-placeholder="Department">{{context.department}}</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 office" data-placeholder="Cell Phone"><span class="kind color-1">t</span>{{context.cell_phone}}</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 email" data-placeholder="E-mail"><span class="kind color-1">e</span>{{context.email}}</p>
                            <p class="absolute size-2 font-2 left-align color-1 placeholder txt-15 web" data-placeholder="Web Address">{{context.web_address}}</p>
                        {% endif %}
                </div>
                <div class="logo-2">
                    <img class="temp-img" alt="logo" src="/media/brochure_staff/Michael-Ohler-FNF-assests/images/logo-2.png">
                </div>
            </div>
        </div>
    </div>


</body></html>
