package com.gwangju.capstonedesign;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.xml.sax.SAXException;
import javax.xml.parsers.ParserConfigurationException;
import java.io.IOException;
import java.util.List;

@Controller
@RequiredArgsConstructor
public class BasicController {
    private final ApiService apiService;

    @GetMapping("/apicall")
    String apicall() throws IOException, ParserConfigurationException, SAXException {
        apiService.callApi();
        return "redirect:/";
    }

    @GetMapping("/")
    String home(Model model){
        List<Item> result = apiService.findDB();
        model.addAttribute("items", result);
        return "index.html";
    }

}