
<!DOCTYPE html>
<!-- saved from url=(0052)http://13.58.114.203/media/templates/pdf/page_4.html -->
<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">

    <title>FRAME</title>
    <style>
        @font-face {
            font-family: 'nexa_boldregular';
            src: url('/media/brochure_staff/fonts/nexa_bold-webfont.woff2') format('woff2'),
                 url('/media/brochure_staff/fonts/nexa_bold-webfont.woff') format('woff');
/*            src: url('./fonts/nexa_bold-webfont.woff2') format('woff2'),
                 url('./fonts/nexa_bold-webfont.woff') format('woff');*/
            font-weight: normal;
            font-style: normal;

        }
        @font-face {
            font-family: 'nexa_lightregular';
            src: url('/media/brochure_staff/fonts/nexa_light-webfont.woff2') format('woff2'),
                 url('/media/brochure_staff/fonts/nexa_light-webfont.woff') format('woff');
/*            src: url('./fonts/nexa_light-webfont.woff2') format('woff2'),
                 url('./fonts/nexa_light-webfont.woff') format('woff');*/
            font-weight: normal;
            font-style: normal;

        }
        @font-face {
            font-family: 'nexa_regularregular';
            src: url('/media/brochure_staff/Michael-Ohler-FNF-assests/fonts/nexaregular-webfont.woff2') format('woff2'),
                 url('/media/brochure_staff/Michael-Ohler-FNF-assests/fonts/nexaregular-webfont.woff') format('woff');
/*            src: url('./fonts/nexaregular-webfont.woff2') format('woff2'),
                 url('./fonts/nexaregular-webfont.woff') format('woff');*/
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
        .flip-vertical {
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
        .TruePath-bg-back {

        }
        .TruePath-bg {
            /* background-image: url('/media/brochure_staff/Claudine-Rousse-FNF-assests/images/Claudine-Rousse-FNF--bg.jpg'); */
            /*background-image: url('./previews/TruePath-Eng.jpg'); */
            background-size: cover;
            background-repeat: no-repeat;
        }
        .background-image {
            position: absolute;
            top: 0mm;
            left: 0mm;
            width: 88.9mm;
            height: 50.8mm;
            img {
                width: 88.9mm;
                height: 50.8mm;
            }
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
            left:11mm;
        }
        .right-align {
            left: 44.5mm;
        }
        .size-0 {
            font-size: 9px;
            margin: 0;
        }
        .size-1 {
            font-size: 9px;
            margin: 0;
        }
        .size-2 {
            font-size: 8.7px;
            margin: 0;
        }
        .color-1 {
            color: #14284b; /*blue*/ 
        }
        .color-2 {
            color: #14284b;/* blue */
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
            top:24.8mm;
        }
        .Address1 {
            top:25.1mm;
        }
        .Address2 {
            top:27.9mm;
        }
        .cell {
            top:32.1mm;
        }
        .office {
            top:34.9mm;
        }
        .fax {
            top:37.7mm;
        }
        .email {
            top:40.5mm;
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
        <div class="template-page TruePath-bg">

            <div class="template-content">
                <div class="background-image">
                    <img class="background-image-img" alt="logo" src="/media/brochure_staff/logos/TruePath-bg.svg" style="width: 88.9mm; height: 50.8mm; display: block;">
                    <!-- <img class="background-image-img" alt="logo" src="./logos/TruePath-bg.svg" style="width: 88.9mm; height: 50.8mm; display: block;"> -->
                </div>
                <div class="text-block">
                        {% if not context %}
                            <p class="absolute size-0 font-1 left-align color-1 placeholder name" data-placeholder="Full Name">Full Name</p>
                            <p class="absolute size-2 font-1 right-align color-2 placeholder txt-upper Address1" data-placeholder="Address1">Address1</p>
                            <p class="absolute size-2 font-1 right-align color-2 placeholder txt-upper Address2" data-placeholder="Address2">Address2</p>

                            <p class="absolute size-2 font-1 right-align color-2 placeholder txt-15 cell" data-placeholder="Cell"><span class="kind color-1">(cell)</span></p>
                            <p class="absolute size-2 font-1 right-align color-2 placeholder txt-15 office" data-placeholder="Office"><span class="kind color-1">(office)</span></p>
                            <p class="absolute size-2 font-1 right-align color-2 placeholder txt-15 fax" data-placeholder="Fax"><span class="kind color-1">(fax)</span></p>
                            <p class="absolute size-2 font-1 right-align color-2 placeholder txt-15 email" data-placeholder="E-mail">E-mail</p>
                        {% else %}
                            <p class="absolute size-0 font-1 left-align color-1 placeholder name" data-placeholder="Full Name">{{context.full_name}}</p>

                            <p class="absolute size-2 font-1 right-align color-2 placeholder txt-upper Address1" data-placeholder="Address1">{{context.address1}}</p>
                            <p class="absolute size-2 font-1 right-align color-2 placeholder txt-upper Address2" data-placeholder="Address2">{{context.address2}}</p>

                            <p class="absolute size-2 font-1 right-align color-2 placeholder txt-15 cell" data-placeholder="Cell">{{context.cell}} <span class="kind color-1">(cell)</span></p>
                            <p class="absolute size-2 font-1 right-align color-2 placeholder txt-15 office" data-placeholder="Office">{{context.office}} <span class="kind color-1">(office)</span></p>
                            <p class="absolute size-2 font-1 right-align color-2 placeholder txt-15 fax" data-placeholder="Fax">{{context.fax}} <span class="kind color-1">(fax)</span></p>
                            <p class="absolute size-2 font-1 right-align color-2 placeholder txt-15 email" data-placeholder="E-mail">{{context.email}}</p>
                        {% endif %}
                </div>
            </div>
        </div>


        <div class="template-page TruePath-bg-back">

            <div class="template-content">
                <div class="back-of-card full-screen">
                    <img class="back-of-card-x" alt="Back" src="/media/brochure_staff/logos/TruePath-back-bg.svg" style="width: 88.9mm; height: 50.8mm; display: block;">
                    <!-- <img class="temp-img" alt="logo" src="./logos/TruePath-back-bg.svg" style="width: 88.9mm; height: 50.8mm; display: block;"> -->
                </div>
                </div>
            </div>
        </div>
    </div>


</body></html>
