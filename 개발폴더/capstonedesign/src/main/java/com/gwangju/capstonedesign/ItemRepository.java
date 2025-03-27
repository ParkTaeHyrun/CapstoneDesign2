package com.gwangju.capstonedesign;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface ItemRepository extends JpaRepository<Item, Integer> {
    Optional findBytmEqk(String tmEqk);
}
