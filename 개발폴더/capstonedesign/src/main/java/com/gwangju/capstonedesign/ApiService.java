package com.gwangju.capstonedesign;

import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import java.io.IOException;
import java.net.URL;
import java.net.URLEncoder;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Component
public class ApiService {
    private final ItemRepository itemRepository;

    @Scheduled(cron = "0 0 */12 * * *")
    public void callApi() throws IOException, ParserConfigurationException, SAXException {
        LocalDate today = LocalDate.now();
        String  enddate = today.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String startdate = today.minusDays(3).format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        StringBuilder urlBuilder = new StringBuilder("http://apis.data.go.kr/1360000/EqkInfoService/getEqkMsg"); /*URL*/
        urlBuilder.append("?" + URLEncoder.encode("serviceKey", "UTF-8") + "=pMymGMt5TX3rHZyVz9agpEYhaZy678NqdYO0wNiji6THFStVZkXJUFfpOjgxNRu7E0d8yBetWXl3H68bcG60bA%3D%3D"); /*Service Key*/
        urlBuilder.append("&" + URLEncoder.encode("pageNo", "UTF-8") + "=" + URLEncoder.encode("1", "UTF-8")); /*페이지번호*/
        urlBuilder.append("&" + URLEncoder.encode("numOfRows", "UTF-8") + "=" + URLEncoder.encode("10", "UTF-8")); /*한 페이지 결과 수*/
        urlBuilder.append("&" + URLEncoder.encode("dataType", "UTF-8") + "=" + URLEncoder.encode("XML", "UTF-8")); /*요청자료형식(XML/JSON)*/
        urlBuilder.append("&" + URLEncoder.encode("fromTmFc", "UTF-8") + "=" + URLEncoder.encode(startdate, "UTF-8")); /*시간(년월일)*/
        urlBuilder.append("&" + URLEncoder.encode("toTmFc", "UTF-8") + "=" + URLEncoder.encode(enddate, "UTF-8")); /*시간(년월일)*/
        URL url = new URL(urlBuilder.toString());
        System.out.println(url);

        DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
        DocumentBuilder dBuilder = dbFactory.newDocumentBuilder();
        Document doc = dBuilder.parse(String.valueOf(url));
        doc.getDocumentElement().normalize();

        NodeList nList = doc.getElementsByTagName("item");
        List<Map<String, Object>> resultitem = new ArrayList<Map<String, Object>>();
        for (int temp = 0; temp < nList.getLength(); temp++) {
            Node nNode = nList.item(temp);

            Element eElement = (Element) nNode;
            String img = getTagValue("img", eElement);
            String loc = getTagValue("loc", eElement);
            String tmEqk = getTagValue("tmEqk", eElement);
            String mt = getTagValue("mt", eElement);

            System.out.println("이미지 주소 : " + img);
            System.out.println("위치 : " + loc);
            System.out.println("시간 : " + tmEqk);
            System.out.println("규모 : " + mt);
            Map<String, Object> result = new HashMap<String, Object>();
            result.put("img", img);
            result.put("loc", loc);
            result.put("tmEqk", tmEqk);
            result.put("mt", mt);
            resultitem.add(result);
        }
        saveDB(resultitem);
    }

    public void saveDB(List<Map<String, Object>> resultitem) {
        for (Map<String, Object> strMap : resultitem) {
            var result = itemRepository.findBytmEqk(String.valueOf(strMap.get("tmEqk")));
            if(result.isPresent()) {
                continue;
            }else {
                Item item = new Item();
                item.img = String.valueOf(strMap.get("img"));
                item.loc = String.valueOf(strMap.get("loc"));
                item.tmEqk = String.valueOf(strMap.get("tmEqk"));
                item.mt = String.valueOf(strMap.get("mt"));
                itemRepository.save(item);
            }
        }
    }

    public List<Item> findDB(){
        return itemRepository.findAll(Sort.by(Sort.Direction.DESC,"tmEqk"));
    }

    public static String getTagValue(String tag, String childTag, Element eElement) {

        //결과를 저장할 result 변수 선언
        String result = "";

        NodeList nlList = eElement.getElementsByTagName(tag).item(0).getChildNodes();

        for(int i = 0; i < eElement.getElementsByTagName(childTag).getLength(); i++) {

            //result += nlList.item(i).getFirstChild().getTextContent() + " ";
            result += nlList.item(i).getChildNodes().item(0).getTextContent() + " ";
        }

        return result;
    }

    public static String getTagValue(String tag, Element eElement) {
        String result = "";

        NodeList nlList = eElement.getElementsByTagName(tag).item(0).getChildNodes();
        result = nlList.item(0).getTextContent();
        return result;
    }

}
