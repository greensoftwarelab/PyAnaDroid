package com.example.sampleapp.ui.home;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;
import com.hunter.library.debug.HunterDebug;
import android.content.Context;

public class HomeViewModel extends ViewModel {

    private MutableLiveData<String> mText;

    @HunterDebug
    public HomeViewModel() {
        mText = new MutableLiveData<>();
        mText.setValue("This is home fragment");
    }

    @HunterDebug
    public LiveData<String> getText() {
        return mText;
    }
}
