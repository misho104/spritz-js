#!/usr/bin/ruby
require 'yomu'

def error msg = "generic error"
  print "Content-type: text/plain\n\nError: #{msg}"
  exit 0
end

def get_options query
  query.split(":")[1..-1]
end

def get_arxiv_id query
  arxiv = query.split(":").shift
  if arxiv =~ /^(\d{7})$/
    return get_url("hep-ph/#{arxiv}")
  elsif arxiv =~ /^[a-z-]{4,10}\/\d{7}$/ or arxiv =~ /^\d{4}\.\d{4,6}$/
    return arxiv
  else
    return nil
  end
end

def to_code arxiv
  get_arxiv_id(arxiv).gsub(/[\.\/]/,"")
end

def redirect html
  print "Content-type: text/html\n\n"
  File.open(html).each do |paragraph|
    print paragraph
  end
  #print "Location: #{html}\n\n"
  exit 0
end

def collapse(text)
  text.gsub!(/\r\n?/, "\n")
  text.gsub!(/\n\n/,  "\n")
  text
end


def format(text)
  text.gsub!(/\r\n?/, "\n")
  text.gsub!(/(\w{2,})-\n(\w{2,})/, '\1\2')
  text.gsub!(/([\w,])\n(\w)/, '\1 \2')
  text
end


arxiv = get_arxiv_id(ENV['QUERY_STRING'])
options = get_options(ENV['QUERY_STRING'])
error('invalid code') unless arxiv

html_name = "yomu_#{to_code(arxiv)}.html"
redirect(html_name) if File.exist?(html_name) and not options.include?("reparse")

xget_result = `./xget.sh #{arxiv} 2>/dev/null`
xget_result.chomp!

error(xget_result) if xget_result =~ /(FAIL|RETRY)/
error("File missing") unless File.exist?(xget_result)

yomu = Yomu.new(xget_result)
text = yomu.text

text = collapse(text) if options.include?("collapse")
text = format(text)

skip = false
File.open(html_name, "w") do |file|
  File.open("demo.html").each do |paragraph|
    paragraph.gsub!(/<<<ID>>>/, arxiv)
    if begin_tag = paragraph.match(/\A(.*<textarea ([^>]* )?id="text".*?>)/)
      file.write(begin_tag)
      file.write(text)
      skip = true
    end
    if skip
      if end_tag = paragraph.match(/<\/textarea>(.*)\z/)
        file.write(end_tag)
        skip = false
      end
    else
      file.write(paragraph)
    end
  end
end
redirect(html_name)

