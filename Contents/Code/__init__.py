# Kink.com
import re

# URLS
EXC_BASEURL = 'http://www.kink.com/'
EXC_SEARCH_MOVIES = EXC_BASEURL + 'search?q=%s'
EXC_MOVIE_INFO = EXC_BASEURL + 'shoot/%s'

def Start():
  HTTP.CacheTime = CACHE_1DAY

class KinkAgent(Agent.Movies):
  name = 'Kink.com'
  languages = [Locale.Language.English]
  accepts_from = ['com.plexapp.agents.localmedia']
  primary_provider = True

  def search(self, results, media, lang):

    title = media.name
    if media.primary_metadata is not None:
      title = media.primary_metadata.title

    episodeMatch = re.match(r'(?:[A-Za-z]{2,4}-)?(\d{3,})', title)

    # if file starts with episode id, just go directly to that episode
    if episodeMatch is not None:
      episodeId = episodeMatch.group(1)
      results.Append(MetadataSearchResult(id = episodeId, name = title, score = 90, lang = lang))

    results.Sort('score', descending=True)

  def update(self, metadata, media, lang):
    html = HTML.ElementFromURL(EXC_MOVIE_INFO % metadata.id,
                               headers={'Cookie': 'viewing-preferences=straight%2Cgay'})

    # studio/tags
    tags = html.xpath('//div[@class="shoot-info"]//a[starts-with(@href,"/tag/")]')
    for tag in tags:
      if tag.get('href').endswith(':channel'):
        metadata.studio = tag.text_content().strip()
      else:
        metadata.tags.add(tag.text_content().strip())
    metadata.genres.add(metadata.studio)

    # set movie title to shoot title
    metadata.title = html.xpath('//div[@class="shoot-info"]//h1')[0].text_content() + " (" + metadata.id + ")"

    # set content rating to XXX
    metadata.content_rating = 'XXX'

    # set episode ID as tagline for easy visibility
    metadata.tagline = metadata.studio + " – " + metadata.id

    # set movie release date to shoot release date
    try:
      release_date = html.xpath('//div[@class="shoot-info"]//p[starts-with(.,"date:")]')[0].text_content().replace('date: ', '')
      metadata.originally_available_at = Datetime.ParseDate(release_date).date()
      metadata.year = metadata.originally_available_at.year
    except: pass

    # set poster to the image that kink.com chose as preview
    try:
      thumbpUrl = html.xpath('//video/@poster')[0]
      thumbp = HTTP.Request(thumbpUrl)
      metadata.posters[thumbpUrl] = Proxy.Media(thumbp)
    except: pass
    
    # fill movie art with all images, so they can be used as backdrops
    try:
      imgs = html.xpath('//div[@id="previewImages"]//img')
      for img in imgs:
        thumbUrl = re.sub(r'/h/[0-9]{3,3}/', r'/h/830/', img.get('src'))
        thumb = HTTP.Request(thumbUrl)
        metadata.art[thumbUrl] = Proxy.Media(thumb)
    except: pass

    # summary
    try:
      metadata.summary = ""
      summary = html.xpath('//div[@class="shoot-info"]/div[@class="description"]')
      if len(summary) > 0:
        for paragraph in summary:
          metadata.summary = metadata.summary + paragraph.text_content().strip().replace('<br>',"\n") + "\n"
        metadata.summary.strip()
    except: pass
    
    # starring/director
    try:
      starring = html.xpath('//p[@class="starring"]/*[@class="names"]/a')
      metadata.roles.clear()
      for member in starring:
        role = metadata.roles.new()
        lename = member.text_content().strip()
        try:
          role.name = lename
        except:
          try:
            role.actor = lename
          except: pass
    except: pass

    # rating
    try:
      rating_dict = JSON.ObjectFromURL(url=EXC_BASEURL + 'api/ratings/%s' % metadata.id,
                                       headers={'Cookie': 'viewing-preferences=straight%2Cgay'})
      metadata.rating = float(rating_dict['avgRating']) * 2
    except: pass
