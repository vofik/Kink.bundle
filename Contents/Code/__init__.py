# Kink.com
import re

# URLS
EXC_BASEURL = 'http://www.kinkondemand.com/'
EXC_SEARCH_MOVIES = EXC_BASEURL + '/kod/search.jsp?search=%s'
EXC_MOVIE_INFO = EXC_BASEURL + 'kod/shoot/%s'

def Start():
  HTTP.CacheTime = CACHE_1DAY
  HTTP.Headers['User-Agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

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
    html = HTML.ElementFromURL(EXC_MOVIE_INFO % metadata.id)
    
    seriesLogo = html.xpath('//div[@id="allShootInfo"]//div[@id="justLogo"]//img')
    if len(seriesLogo) > 0:
      series = seriesLogo[0].get('alt')
    else:
      series = html.xpath('//div[@id="allShootInfo"]//div[@id="justLogo"]')[0].text_content().strip('\t\r\n ')

    # set movie studio to kink site
    metadata.studio = series

    # set movie title to shoot title
    metadata.title = html.xpath('//div[@id="shootHeader"]/h1')[0].text_content() + " (" + metadata.id + ")"

    # set rating to XXX
    metadata.content_rating = 'XXX'
    metadata.genres.add(series)
    metadata.director = html.xpath('//div[@class="titleAndPerformers"]/meta[@itemprop="director"]/@content')[0].text_content().strip('\t\r\n ')

    #set episode ID as tagline for easy visibility
    metadata.tagline = series + " – " + metadata.id

    # set movie release date to shoot release date
    try:
      release_date = html.xpath('//div[@class="titleAndPerformers"]//p')[0].text_content().split('-')[0].strip(' ')
      metadata.originally_available_at = Datetime.ParseDate(release_date).date()
      metadata.year = metadata.originally_available_at.year
    except: pass


    # set poster to the image that kink.com chose as preview
    try:
      thumbselection = html.xpath('//div[@class="titleAndPerformers"]/meta[@itemprop="image"]/@content')[0]
      thumbpUrl = re.sub(r'/h/[0-9]{3,3}/', r'/h/830/', thumbselection)
      thumbp = HTTP.Request(thumbpUrl)
      metadata.posters[thumbpUrl] = Proxy.Media(thumbp)
    except: pass
    
    # fill movie art with all images, so they can be used as backdrops
    try:
      imgs = html.xpath('//table[@class="fullViewTable"]//img')
      for img in imgs:
        thumbUrl = re.sub(r'/h/[0-9]{3,3}/', r'/h/830/', img.get('src'))
        thumb = HTTP.Request(thumbUrl)
        metadata.art[thumbUrl] = Proxy.Media(thumb)
    except: pass

    # summary
    try:
      metadata.summary = ""
      summary = html.xpath('//div[@class="shootDescription"]/p[@class="description"]')
      if len(summary) > 0:
        for paragraph in summary:
          metadata.summary = metadata.summary + paragraph.text_content().strip(' \n\r\t').replace('<br>',"\n") + "\n"
        metadata.summary.strip('\n')
    except: pass
    
    # starring/director
    try:
      starring = html.xpath('//div[@class="titleAndPerformers"]//a')
      metadata.directors.clear()
      metadata.roles.clear()
      thedirector = html.xpath('//div[@class="titleAndPerformers"]/meta[@itemprop="director"]/@content')[0]
      metadata.directors.add(thedirector)
      for member in starring:
        role = metadata.roles.new()
        lename = member.text_content().strip(' ')
        role.actor = lename
    except: pass
