# Kink.com
import re

# URLS
EXC_BASEURL = 'http://www.kinkondemand.com/'
EXC_SEARCH_MOVIES = EXC_BASEURL + '/kod/search.jsp?search=%s'
EXC_MOVIE_INFO = EXC_BASEURL + 'kod/shoot/%s'

def Start():
  HTTP.CacheTime = CACHE_1DAY
  HTTP.SetHeader('User-agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)')

class KinkAgent(Agent.Movies):
  name = 'Kink.com'
  languages = [Locale.Language.English]
  accepts_from = ['com.plexapp.agents.localmedia']
  primary_provider = True

  def search(self, results, media, lang):

    title = media.name
    if media.primary_metadata is not None:
      title = media.primary_metadata.title

    Log('searching for : ' + title)

    if title.startswith('The '):
      title = title.replace('The ','',1)

    episodeMatch = re.match(r'(\d{3,})', title)

    # if file starts with episode id, just go directly to that episode
    if episodeMatch is not None:
      episodeId = episodeMatch.group(1)
      results.Append(MetadataSearchResult(id = episodeId, name = title, score = 90, lang = lang))

    results.Sort('score', descending=True)

  def update(self, metadata, media, lang):
    Log("---------")
    Log(EXC_MOVIE_INFO % metadata.id)
    
    html = HTML.ElementFromURL(EXC_MOVIE_INFO % metadata.id)
    
    seriesLogo = html.xpath('//div[@id="allShootInfo"]//div[@id="justLogo"]//img')
    if len(seriesLogo) > 0:
      series = seriesLogo[0].get('alt')
    else:
      series = html.xpath('//div[@id="allShootInfo"]//div[@id="justLogo"]')[0].text_content().strip('\t\r\n ')

    metadata.title = series + ' - ' + html.xpath('//div[@id="shootHeader"]/h1')[0].text_content()

    metadata.content_rating = 'XXX'
    metadata.studio = 'Kink.com'
    # metadata.genres = None

    # Release Date
    try:
      release_date = html.xpath('//div[@class="titleAndPerformers"]//p')[0].text_content().split('-')[0].strip(' ')
      metadata.originally_available_at = Datetime.ParseDate(release_date).date()
      metadata.year = metadata.originally_available_at.year
    except:
      Log("could not parse release date %s", release_date)
      pass

    # Get Thumb and Poster
    try:
      img = html.xpath('//table[@class="fullViewTable"]//img')[0]
      thumbUrl = img.get('src')
      thumb = HTTP.Request(thumbUrl)
      metadata.posters[thumbUrl] = Proxy.Media(thumb)
    except: pass

    # Summary.
    try:
      metadata.summary = ""
      summary = html.xpath('//div[@class="shootDescription"]/p[@class="description"]')
      if len(summary) > 0:
        for paragraph in summary:
          metadata.summary = metadata.summary + paragraph.text_content().strip(' \n\r\t').replace('<br>',"\n") + "\n"
        metadata.summary.strip('\n')
    except: pass

    # Genre.
    # try:
    #   metadata.genres.clear()
    #   genres = html.xpath('//table[@width="620"]//table[@width="620"]//a[contains(@href, "DVD/Categories")]')
    # 
    #   if len(genres) > 0:
    #     for genreLink in genres:
    #       genreName = genreLink.text_content().strip('\n')
    #       if len(genreName) > 0 and re.match(r'View Complete List', genreName) is None:
    #         metadata.genres.add(genreName)
    # except: pass

    # Starring
    try:
      starring = html.xpath('//div[@class="titleAndPerformers"]//a')
      metadata.roles.clear()
      for member in starring:
        role = metadata.roles.new()
        role.actor = member.text_content().strip(' ')

        Log('Starring: ' + role.actor)
    except: pass
