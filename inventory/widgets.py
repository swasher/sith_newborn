# coding: utf-8
import cloudinary
import humanfriendly
from cloudinary.api import RateLimited
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import AdminFileWidget

class AdminCloudinaryWidget(AdminFileWidget):

    #template_with_initial = ('%(initial_text)s: <a href="%(initial_url)s">%(initial)s</a> %(clear_template)s<br />%(input_text)s: %(input)s')
    # override:
    template_with_initial = ''

    #template_with_clear = '%(clear)s <label for="%(clear_checkbox_id)s">%(clear_checkbox_label)s</label>'
    # override:
    template_with_clear = ''

    template_pict = """
    <div>
        <a href="{picture_full}"
                class="featherlight-loading tooltip"
                title="Caption: {caption}<p>Alt: {alt}<p>{filesize}"
                data-featherlight="image"
                alt="{alt}"
                target="_blank" >
            {picture_preview}
        </a>
    </div>
    <div>
        <a href="{cloudinary_prefix}{public_id}" target="_blank">
            Cloudinary Link
        </a>
    </div>
    """

    template_pdf =  """
    <div>
        <a href="{picture_full}"
                class="tooltip"
                title="Caption: {caption}<p>
                    Alt: {alt}<p>
                    {filesize}"
                alt="{alt}"
                target="_blank" >
            {picture_preview}
        </a>
    </div>
    <div>
        <a href="{cloudinary_prefix}{public_id}" target="_blank">
            Cloudinary Link
        </a>
    </div>
    """

    class Media:
        css = {
            'all': ('https://cdn.rawgit.com/iamceege/tooltipster/master/dist/css/tooltipster.bundle.min.css',
                    'https://cdn.rawgit.com/iamceege/tooltipster/master/dist/css/plugins/tooltipster/sideTip/themes/tooltipster-sideTip-light.min.css',)
        }
        js = ('https://cdn.rawgit.com/iamceege/tooltipster/master/dist/js/tooltipster.bundle.min.js',)


    def render(self, name, value, attrs=None):

        import html

        output = []
        cloudinary_prefix = 'https://cloudinary.com/console/media_library#/dialog/image/upload/'

        if value and getattr(value, "url", None):
            try:
                image_exist = cloudinary.api.resource(value.public_id)
            except cloudinary.api.NotFound:
                image_exist = None
                dummy_pict = 'cloudinary_id_not_found.jpg'
            except RateLimited:
                image_exist = None
                dummy_pict = 'cloudinary_rate_exceed.jpg'

            if image_exist:
                try:
                    file_format = cloudinary.api.resource(value.public_id)['format']
                except AttributeError:
                    file_format = None

                try:
                    caption = html.escape(cloudinary.api.resource(value.public_id)['context']['custom']['caption'])
                except KeyError:
                    caption = '<br>'

                try:
                    alt = html.escape(cloudinary.api.resource(value.public_id)['context']['custom']['alt'])
                except KeyError:
                    alt = "Image does't exist"

                fs = cloudinary.api.resource(value.public_id)['bytes']
                filesize = humanfriendly.format_size(fs)
                picture_preview = cloudinary.CloudinaryImage(value.public_id).image(format='JPG', width = 150, height = 150, crop = 'fill', alt = alt) # html TAG 'a' with a small pict
                picture_full = cloudinary.CloudinaryImage(value.public_id).build_url()                                                                 # http link to full pict

            else:
                picture_full = '/static/'.format(dummy_pict)
                picture_preview = "<img height = '150' width = '150' src='/static/{}'>".format(dummy_pict)
                caption = 'Probably, Cloudinary content was removed.'
                alt = 'Missed ID: {}'.format(value.public_id)
                filesize = ''
                file_format = 'jpg'

            if file_format in ['pdf']:
                template = self.template_pdf
            else:
                template = self.template_pict

            html = template.format(picture_full=picture_full,
                                   caption=caption,
                                   filesize=filesize,
                                   picture_preview = picture_preview,
                                   cloudinary_prefix=cloudinary_prefix,
                                   public_id=value.public_id,
                                   alt=alt,
                                   )

            output.append(html)

        output.append(super(AdminFileWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))