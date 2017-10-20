
<!DOCTYPE html>
<!-- saved from url=(0052)http://13.58.114.203/media/templates/pdf/page_4.html -->
<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">

    <title>FRAME</title>
    <style>
        @font-face {
            font-family: 'nexa_boldregular';
            src: url('/media/brochure_staff/Claudine-Rousse-FNF-assests/fonts/nexa_bold-webfont.woff2') format('woff2'),
                 url('/media/brochure_staff/Claudine-Rousse-FNF-assests/fonts/nexa_bold-webfont.woff') format('woff');
            font-weight: normal;
            font-style: normal;

        }
        @font-face {
            font-family: 'nexa_lightregular';
            src: url('/media/brochure_staff/Claudine-Rousse-FNF-assests/fonts/nexa_light-webfont.woff2') format('woff2'),
                 url('/media/brochure_staff/Claudine-Rousse-FNF-assests/fonts/nexa_light-webfont.woff') format('woff');
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
            /*background: #117f46;*/
            /*border: 1px solid #333;*/
            width: 88.9mm;
            height: 50.8mm;
            position: relative;
            page-break-after: always;
        }
        .claudine-bg-invert-x {
            background-image: url('/media/brochure_staff/Claudine-Rousse-FNF-assests/images/Claudine-Rousse-FNF--bg-invert.jpg');
            background-image: url('/media/brochure_staff/Claudine-Rousse-FNF-assests/images/Claudine-Rousse-FNF--bg.jpg');
            background-size: cover;
            background-repeat: no-repeat;
        }
        .claudine-bg {
            /*background-image: url('/media/brochure_staff/Claudine-Rousse-FNF-assests/images/Claudine-Rousse-FNF--bg.jpg');*/
             /*background-image: url('./Claudine-Rousse-FNF-assests/images/Claudine-Rousse-FNF--bg.jpg'); */
            background-size: cover;
            background-repeat: no-repeat;
        }
        .logo-1 {
            position: absolute;
            top: 6.4mm;
            width: 194px;
            height: 41px;
            img {
                width: 194px;
                height: 41px;
            }
        }
        .logo-2 {
            position: absolute;
            top: 36.4mm;
            right: 6.3mm;
            width: 122px;
            height: 31px;
            img {
                width: 122px;
                height: 31px;
            }
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
        .size-0 {
            font-size: 12px;
            margin: 0;
        }
        .size-1 {
            font-size: 12px;
            margin: 0;
        }
        .size-2 {
            font-size: 9.5px;
            margin: 0;
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
        .position span {
            font-weight: normal;
            font-size: 9.9px;
        }
        .position2 {
            top:27.7mm;
            text-transform: uppercase;
        }
        .office {
            top:29.5mm;
        }
        .cell {
            top:32.5mm;
        }
        .fax {
            top:35.8mm;
        }
        .email {
            top:38.9mm;
        }
        .web {
            top: 42mm;
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
        <div class="template-page claudine-bg">

            <div class="template-content">
                <div class="logo-1 left-align">
                    <img class="temp-img" alt="logo" src="/media/brochure_staff/logos/fnf-canada.svg" style="width: 194px; height: 41px; display: block;">
                    <!-- <img class="temp-img" alt="logo" src="./logos/fnf-canada.svg"> -->
                </div>
                <div class="text-block">
<!--                         <p class="usertext1 placeholder" data-placeholder="Text 3">{{context.text3}}</p> -->
                        {% if not context %}
                            <p class="absolute size-0 font-2 left-align color-1 placeholder name" data-placeholder="Full Name">Full Name</p>
                            <p class="absolute size-2 font-2 left-align color-2 placeholder txt-upper position" data-placeholder="Position">Position <span class="font-1" data-placeholder="Department">Department</span></p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 office" data-placeholder="Office Phone"><span class="kind color-1">o</span>Office Phone</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 cell" data-placeholder="Cell"><span class="kind color-1">c</span>Cell</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 fax" data-placeholder="Fax"><span class="kind color-1">f</span>Fax</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 email" data-placeholder="E-mail"><span class="kind color-1">e</span>E-mail</p>
                            <p class="absolute size-2 font-2 left-align color-1 placeholder txt-15 web">Web Address</p>
                        {% else %}
                            <p class="absolute size-0 font-2 left-align color-1 placeholder name" data-placeholder="Full Name">{{context.full_name}}</p>
                            <p class="absolute size-2 font-2 left-align color-2 placeholder txt-upper position" data-placeholder="Position">{{context.position}} <span class="font-1" data-placeholder="Department">{{context.department}}</span></p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 office" data-placeholder="Office Phone"><span class="kind color-1">o</span> {{context.office_phone}}</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 cell" data-placeholder="Cell"><span class="kind color-1">c</span> {{context.cell}} </p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 fax" data-placeholder="Fax"><span class="kind color-1">f</span> {{context.fax}}</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 email" data-placeholder="E-mail"><span class="kind color-1">e</span> {{context.email}}</p>
                            <p class="absolute size-2 font-2 left-align color-1 placeholder txt-15 web" data-placeholder="Web Address">{{context.web_address}}</p>
                        {% endif %}
                </div>
                <div class="logo-2">
                    <img class="temp-img" alt="logo" src="/media/brochure_staff/logos/smartchoice.svg" style="width: 122px;height: 31px;display: block;">
                    <!-- <img class="temp-img" alt="logo" src="./logos/smartchoice.svg"> -->
                </div>
            </div>
        </div>


        <div class="template-page claudine-bg">

            <div class="template-content">
                <div class="logo-1 left-align">
                    <img class="temp-img" alt="logo" src="/media/brochure_staff/logos/fnf-canada.svg" style="width: 194px; height: 41px; display: block;">
                    <!-- <img class="temp-img" alt="logo" src="./logos/fnf-canada.svg"> -->
                </div>
                <div class="text-block">
<!--                         <p class="usertext1 placeholder" data-placeholder="Text 3">{{context.text3}}</p> -->
                        {% if not context %}
                            <p class="absolute size-0 font-2 left-align color-1 placeholder name" data-placeholder="Full Name-French">Full Name-French</p>
                            <p class="absolute size-2 font-2 left-align color-2 placeholder txt-upper position" data-placeholder="Position-French">Position-French <span class="font-1" data-placeholder="Department-French">- Department-French</span></p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 office" data-placeholder="Text 11"><span class="kind color-1" data-placeholder="Office Phone-French">o</span>Office Phone-French</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 cell" data-placeholder="Cell-French"><span class="kind color-1">c </span>Cell-French</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 fax" data-placeholder="Fax-French"><span class="kind color-1">f</span>Fax-French</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 email" data-placeholder="Email-French"><span class="kind color-1">e</span>Email-French</p>
                            <p class="absolute size-2 font-2 left-align color-1 placeholder txt-15 web" data-placeholder="Web-French">Web-French</p>
                        {% else %}
                            <p class="absolute size-0 font-2 left-align color-1 placeholder name" data-placeholder="Full Name-French">{{context.full_name_french}}</p>
                            <p class="absolute size-2 font-2 left-align color-2 placeholder txt-upper position" data-placeholder="Position-French">{{context.position_french}} <span class="font-1" data-placeholder="Department-French">- {{context.department_french}}</span></p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 office" data-placeholder="Office Phone-French"><span class="kind color-1">o</span> {{context.office_phone_french}}</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 cell" data-placeholder="Cell-French"><span class="kind color-1">c </span> {{context.cell_french}}</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 fax" data-placeholder="Fax-French"><span class="kind color-1">f</span> {{context.fax_french}}</p>
                            <p class="absolute size-2 font-1 left-align color-3 placeholder txt-15 email" data-placeholder="Email-French"><span class="kind color-1">e</span> {{context.email_french}}</p>
                            <p class="absolute size-2 font-2 left-align color-1 placeholder txt-15 web" data-placeholder="Web-French">{{context.web_french}}</p>
                        {% endif %}
                </div>
                <div class=" logo-2">
                    <img class="temp-img" alt="logo" src="/media/brochure_staff/logos/smartchoice.svg" style="width: 122px;height: 31px;display: block;">
                    <!-- <img class="temp-img" alt="logo" src="./logos/smartchoice.svg"> -->
                </div>
            </div>
        </div>
    </div>


</body></html>
